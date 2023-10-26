# EV Automation
This project aims to add some simple automation and control around
my GivEnergy home solar/battery system, Andersen A2 EV charger and
Renault electric vehicle.

## Goals
- Charge the house battery or the car from solar, but not at the same time
- Do not discharge the house battery when charging the car
- Charge the car from grid when offpeak, otherwise from solar
- Provide an API which can be invoked from an Alexa skill to give voice control

## Current State
I've scaled back the goals for the winter when there's not enough solar
energy to charge the vehicle anyway. Right now it just enables grid charging
at offpeak hours. This will serve to check whether the end/start of DST is
handled correctly, and if the Andersen session needs reauthenticated over
time.

## Running
* `python -m .venv`
* `source .venv/bin/activate`
* `pip install -r requirements.txt`
* `python main.py`

## Runtime Configuration
The following environment variables are required:
* `ANDERSEN_USERNAME` - login username for Andersen API
* `ANDERSEN_PASSWORD` - login password for Andersen API
* `ANDERSEN_DEVICE_NAME` - name of Andersen charger
