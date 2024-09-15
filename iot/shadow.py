# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from awscrt import mqtt, http
from awsiot import iotshadow, mqtt_connection_builder
from concurrent.futures import Future
from time import sleep
from typing import Any, Callable
from uuid import uuid4
import logging
import sys
import threading
import traceback

# - Overview -
# This sample uses the AWS IoT Device Shadow Service to keep a property in
# sync between device and server. Imagine a light whose color may be changed
# through an app, or set by a local user.
#
# - Instructions -
# Once connected, type a value in the terminal and press Enter to update
# the property's "reported" value. The sample also responds when the "desired"
# value changes on the server. To observe this, edit the Shadow document in
# the AWS Console and set a new "desired" value.
#
# - Detail -
# On startup, the sample requests the shadow document to learn the property's
# initial state. The sample also subscribes to "delta" events from the server,
# which are sent when a property's "desired" value differs from its "reported"
# value. When the sample learns of a new desired value, that value is changed
# on the device and an update is sent to the server with the new "reported"
# value.


class LockedData:
    def __init__(self):
        self.lock = threading.Lock()
        self.shadow_value = None
        self.disconnect_called = False
        self.request_tokens = set()


class IoTClient:
    def __init__(self):
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint="aa40w08kkflrp-ats.iot.eu-west-1.amazonaws.com",
            cert_filepath="./thing.crt",
            pri_key_filepath="./thing-private.pem.key",
            ca_filepath="./AmazonRootCA1.pem",
            client_id="car_iot",
            clean_session=False,
            keep_alive_secs=30,
        )

        print("Connecting to endpoint with client ID")

        connected_future = mqtt_connection.connect()

        self._shadow_client = iotshadow.IotShadowClient(mqtt_connection)

        # Wait for connection to be fully established.
        # Note that it's not necessary to wait, commands issued to the
        # mqtt_connection before its fully connected will simply be queued.
        # But this sample waits here so it's obvious when a connection
        # fails or succeeds.
        connected_future.result()
        print("Connected!")

    def register_thing(
        self,
        thing_name: str,
        property: str,
        default_value: Any,
        callback: Callable[[str], None] | None = None,
    ) -> "IoTThing":
        return IoTThing(
            self._shadow_client, thing_name, property, default_value, callback
        )


class IoTThing:
    def __init__(
        self,
        shadow_client: IoTClient,
        thing_name: str,
        property: str,
        default_value: Any,
        callback: Callable[[str], None] | None = None,
    ):
        self._shadow_client = shadow_client
        self._thing_name = thing_name
        self._callback = callback
        self._property = property
        self._default_value = default_value
        self._locked_data = LockedData()

        try:
            # Note that is **is** important to wait for "accepted/rejected" subscriptions
            # to succeed before publishing the corresponding "request".
            print("Subscribing to Update responses...")
            update_accepted_subscribed_future, _ = (
                shadow_client.subscribe_to_update_shadow_accepted(
                    request=iotshadow.UpdateShadowSubscriptionRequest(
                        thing_name=thing_name
                    ),
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self._on_update_shadow_accepted,
                )
            )

            update_rejected_subscribed_future, _ = (
                shadow_client.subscribe_to_update_shadow_rejected(
                    request=iotshadow.UpdateShadowSubscriptionRequest(
                        thing_name=thing_name
                    ),
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self._on_update_shadow_rejected,
                )
            )

            # Wait for subscriptions to succeed
            update_accepted_subscribed_future.result()
            update_rejected_subscribed_future.result()

            print("Subscribing to Get responses...")
            get_accepted_subscribed_future, _ = (
                shadow_client.subscribe_to_get_shadow_accepted(
                    request=iotshadow.GetShadowSubscriptionRequest(
                        thing_name=thing_name
                    ),
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self._on_get_shadow_accepted,
                )
            )

            get_rejected_subscribed_future, _ = (
                shadow_client.subscribe_to_get_shadow_rejected(
                    request=iotshadow.GetShadowSubscriptionRequest(
                        thing_name=thing_name
                    ),
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self._on_get_shadow_rejected,
                )
            )

            # Wait for subscriptions to succeed
            get_accepted_subscribed_future.result()
            get_rejected_subscribed_future.result()

            if callback:
                print("Subscribing to Delta events...")
                delta_subscribed_future, _ = (
                    shadow_client.subscribe_to_shadow_delta_updated_events(
                        request=iotshadow.ShadowDeltaUpdatedSubscriptionRequest(
                            thing_name=thing_name
                        ),
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                        callback=self._on_shadow_delta_updated,
                    )
                )

                # Wait for subscription to succeed
                delta_subscribed_future.result()

                # Issue request for shadow's current state.
                # The response will be received by the on_get_accepted() callback
                print("Requesting current shadow state...")

                with self._locked_data.lock:
                    # use a unique token so we can correlate this "request" message to
                    # any "response" messages received on the /accepted and /rejected topics
                    token = str(uuid4())

                    publish_get_future = shadow_client.publish_get_shadow(
                        request=iotshadow.GetShadowRequest(
                            thing_name=thing_name, client_token=token
                        ),
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                    )

                    self._locked_data.request_tokens.add(token)

                # Ensure that publish succeeds
                publish_get_future.result()

        except Exception as e:
            logging.error("IoTThing()", e)

    def _on_get_shadow_accepted(self, response):
        # type: (iotshadow.GetShadowResponse) -> None
        try:
            with self._locked_data.lock:
                # check that this is a response to a request from this session
                try:
                    self._locked_data.request_tokens.remove(response.client_token)
                except KeyError:
                    print(
                        "Ignoring get_shadow_accepted message due to unexpected token."
                    )
                    return

                print("Finished getting initial shadow state.")
                if self._locked_data.shadow_value is not None:
                    print(
                        "  Ignoring initial query because a delta event has already been received."
                    )
                    return

            if response.state:
                if response.state.delta:
                    value = response.state.delta.get(self._property)
                    if value:
                        print("  Shadow contains delta value '{}'.".format(value))
                        self.change_shadow_value(value)
                        if self._callback:
                            self._callback(value)
                        return

                if response.state.reported:
                    value = response.state.reported.get(self._property)
                    if value:
                        print("  Shadow contains reported value '{}'.".format(value))
                        self.set_local_value_due_to_initial_query(
                            response.state.reported[self._property]
                        )
                        return

            print(
                "  Shadow document lacks '{}' property. Setting defaults...".format(
                    self._property
                )
            )
            self.change_shadow_value(self._default_value)
            return

        except Exception as e:
            logging.error("_on_get_shadow_accepted", e)

    def _on_get_shadow_rejected(self, error):
        # type: (iotshadow.ErrorResponse) -> None
        try:
            # check that this is a response to a request from this session
            with self._locked_data.lock:
                try:
                    self._locked_data.request_tokens.remove(error.client_token)
                except KeyError:
                    print(
                        "Ignoring get_shadow_rejected message due to unexpected token."
                    )
                    return

            if error.code == 404:
                print("Thing has no shadow document. Creating with defaults...")
                self.change_shadow_value(self._default_value)
            else:
                logging.error(
                    "Get request was rejected. code:{} message:'{}'".format(
                        error.code, error.message
                    )
                )

        except Exception as e:
            logging.error("_on_get_shadow_rejected", e)

    def _on_shadow_delta_updated(self, delta):
        # type: (iotshadow.ShadowDeltaUpdatedEvent) -> None
        try:
            print("Received shadow delta event.")
            if delta.state and (self._property in delta.state):
                value = delta.state[self._property]
                if value is None:
                    print(
                        "  Delta reports that '{}' was deleted. Resetting defaults...".format(
                            self._property
                        )
                    )
                    self.change_shadow_value(self._default_value)
                    return
                else:
                    print(
                        "  Delta reports that desired value is '{}'. Changing local value...".format(
                            value
                        )
                    )
                    if delta.client_token is not None:
                        print("  ClientToken is: " + delta.client_token)
                    self.change_shadow_value(value)
                if self._callback:
                    self._callback(value)
            else:
                print("  Delta did not report a change in '{}'".format(self._property))

        except Exception as e:
            logging.error("_on_shadow_delta_updated", e)

    def _on_publish_update_shadow(self, future):
        # type: (Future) -> None
        try:
            future.result()
            print("Update request published.")
        except Exception as e:
            print("Failed to publish update request.")
            logging.error("_on_publish_update_shadow", e)

    def _on_update_shadow_accepted(self, response):
        # type: (iotshadow.UpdateShadowResponse) -> None
        try:
            # check that this is a response to a request from this session
            with self._locked_data.lock:
                try:
                    self._locked_data.request_tokens.remove(response.client_token)
                except KeyError:
                    print(
                        "Ignoring update_shadow_accepted message due to unexpected token."
                    )
                    return

            try:
                if response.state.reported is not None:
                    if self._property in response.state.reported:
                        print(
                            "Finished updating reported shadow value to '{}'.".format(
                                response.state.reported[self._property]
                            )
                        )  # type: ignore
                    else:
                        print("Could not find shadow property with name: '{}'.".format(self._property))  # type: ignore
                else:
                    print(
                        "Shadow states cleared."
                    )  # when the shadow states are cleared, reported and desired are set to None
            except BaseException:
                exit("Updated shadow is missing the target property")

        except Exception as e:
            logging.error("_on_update_shadow_accepted", e)

    def _on_update_shadow_rejected(self, error):
        # type: (iotshadow.ErrorResponse) -> None
        try:
            # check that this is a response to a request from this session
            with self._locked_data.lock:
                try:
                    self._locked_data.request_tokens.remove(error.client_token)
                except KeyError:
                    print(
                        "Ignoring update_shadow_rejected message due to unexpected token."
                    )
                    return

            exit(
                "Update request was rejected. code:{} message:'{}'".format(
                    error.code, error.message
                )
            )

        except Exception as e:
            logging.error("_on_update_shadow_rejected", e)

    def set_local_value_due_to_initial_query(self, reported_value):
        with self._locked_data.lock:
            self._locked_data.shadow_value = reported_value
        if self._callback:
            self._callback(reported_value)

    def change_shadow_value(self, value):
        with self._locked_data.lock:
            if self._locked_data.shadow_value == value:
                print("Local value is already '{}'.".format(value))
                return

            print("Changed local shadow value to '{}'.".format(value))
            self._locked_data.shadow_value = value

            print("Updating reported shadow value to '{}'...".format(value))

            # use a unique token so we can correlate this "request" message to
            # any "response" messages received on the /accepted and /rejected topics
            token = str(uuid4())

            # if the value is "clear shadow" then send a UpdateShadowRequest with None
            # for both reported and desired to clear the shadow document completely.
            if value == "clear_shadow":
                tmp_state = iotshadow.ShadowState(
                    reported=None,
                    desired=None,
                    reported_is_nullable=True,
                    desired_is_nullable=True,
                )
                request = iotshadow.UpdateShadowRequest(
                    thing_name=self._thing_name,
                    state=tmp_state,
                    client_token=token,
                )
            # Otherwise, send a normal update request
            else:
                # if the value is "none" then set it to a Python none object to
                # clear the individual shadow property
                if value == "none":
                    value = None

                request = iotshadow.UpdateShadowRequest(
                    thing_name=self._thing_name,
                    state=iotshadow.ShadowState(
                        reported={self._property: value},
                        desired={self._property: value},
                    ),
                    client_token=token,
                )

            future = self._shadow_client.publish_update_shadow(
                request, mqtt.QoS.AT_LEAST_ONCE
            )

            self._locked_data.request_tokens.add(token)

            future.add_done_callback(self._on_publish_update_shadow)
