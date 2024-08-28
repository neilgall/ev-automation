from dataclasses import dataclass
import boto3
import datetime as dt
import json

from model import ChargeIntent, charge_intent, prune_charge_intent_dict


iot_data = boto3.client('iot-data')


def set_hvac(enable: bool):
    desired_state = "on" if enable else "off"
        
    desired_shadow = {
        "state": {
            "desired": {
                "state": desired_state
            }
        }
    }
    iot_data.update_thing_shadow(
        thingName="car_heater",
        payload=json.dumps(desired_shadow)
    )

    return enable


def set_charge_level(target_charge_level: int, target_charge_date: dt.date) -> ChargeIntent:
    shadow = iot_data.get_thing_shadow(thingName="car_status", shadowName="charge_intent")
    charge_intent_by_date = json.load(shadow['payload'])

    charge_intent_by_date = prune_charge_intent_dict(
        charge_intent_by_date,
        dt.datetime.now()
    )
    intent = charge_intent(target_charge_level, target_charge_date, dt.datetime.now())
    charge_intent_by_date = intent.update_dict(charge_intent_by_date)

    desired_shadow = {
        "state": {
            "desired": charge_intent_by_date
        }
    }

    iot_data.update_thing_shadow(
        thingName="car_status",
        shadowName="charge_intent",
        payload=json.dumps(desired_shadow)
    )

    return intent


@dataclass
class BatteryLevel:
    battery_percentage: int | None
    range_km: int | None


def get_battery_level() -> BatteryLevel:
    shadow = iot_data.get_thing_shadow(thingName="car_status")
    status = json.load(shadow['payload'])

    data = status.get("state", {}).get("reported", {}).get("state", {})
    battery_level = data.get("battery_level")
    range_km = data.get("estimated_range")

    return BatteryLevel(battery_level, range_km)
