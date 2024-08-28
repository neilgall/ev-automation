# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import json
import logging
import ask_sdk_core.utils as ask_utils
import datetime as dt

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

from model import ChargeIntent
from iot_data import set_hvac, set_charge_level, BatteryLevel, get_battery_level


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_slot(slots, name, default_value):
    slot = slots.get(name)
    return slot.value if slot and slot.value else default_value


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome. Which would you like to try?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class HvacIntentHandler(AbstractRequestHandler):
    """Handler for enable_hvac and disable_hvac intents"""

    IS_ENABLE = ask_utils.is_intent_name("enable_hvac")
    IS_DISABLE = ask_utils.is_intent_name("disable_hvac")
    
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return HvacIntentHandler.IS_ENABLE(handler_input) or HvacIntentHandler.IS_DISABLE(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        enable = HvacIntentHandler.IS_ENABLE(handler_input)
        if set_hvac(enable):
            speak_output = "Car heating started"
        else:
            speak_output = "Car heating stopped"
            
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class ChargeLevelIntentHandler(AbstractRequestHandler):
    """Handler for set charge level intent"""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("set_charge_target")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots
        target_charge_level = get_slot(slots, "charge_level", 60)
        target_charge_date = get_slot(slots, "date", dt.date.today())

        if type(target_charge_date) == str:
            target_charge_date = dt.date.fromisoformat(target_charge_date)

        intent = set_charge_level(target_charge_level, target_charge_date)

        speak_output = f"Ok, your car will charge to {intent.battery_percentage} percent on {intent.date}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .set_card(SimpleCard("Car Charging", speak_output))
                .response
        )


class CarStatusIntentHandler(AbstractRequestHandler):
    """Handler for get_battery_level intent"""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("get_battery_level")(handler_input)

    def handle(self, handler_input):
        battery_level = get_battery_level()

        if battery_level.battery_percentage is None:
            speak_output = "I'm sorry, I wasn't able to read the current battery level"
        else:
            speak_output = f"Your car battery is at {battery_level.battery_percentage} percent."

        if battery_level.range_km is not None:
            range_miles = int(battery_level.range_km / 1.609344)
            speak_output += f" The estimated range is {range_miles} miles."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .set_card(SimpleCard("Car Battery", speak_output))
                .response
        )


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(HvacIntentHandler())
sb.add_request_handler(ChargeLevelIntentHandler())
sb.add_request_handler(CarStatusIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()