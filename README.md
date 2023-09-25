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
This is currently experimental. Access to the three main components
is implemented and a simple model and controller are in development.

## Running
* `python -m .venv`
* `source .venv/bin/activate`
* `pip install -r requirements.txt`
* `uvicorn server:app`

## Runtime Configuration
The following environment variables are required:
* `ANDERSEN_USERNAME` - login username for Andersen API
* `ANDERSEN_PASSWORD` - login password for Andersen API
* `ANDERSEN_DEVICE_NAME` - name of Andersen charger
* `RENAULT_USERNAME` - login username for Renault API
* `RENAULT_PASSWORD` - login password for Renault API
* `RENAULT_REGISTRATION` - vehicle registration plate
* `GIVENERGY_IPADDRESS` - local IP address of GivEnergy dongle
