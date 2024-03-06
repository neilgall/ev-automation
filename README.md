# EV Automation
This project aims to automate charging my Renault electric vehicle to make
maximum use of any excess power from my home solar panels.

## Current State
* Controls just the max-solar level on the Andersen A2 EV charger
* Charges the car to a default of 60% by grid energy on cheap rate at night
* Default can be overridden by writing to an AWS iot-data thing shadow
* Excess solar goes to the car

## Running
* `python -m .venv`
* `source .venv/bin/activate`
* `make requirements`
* `python main.py`

## Runtime Configuration
The following environment variables are required:
* `ANDERSEN_USERNAME` - login username for Andersen API
* `ANDERSEN_PASSWORD` - login password for Andersen API
* `ANDERSEN_DEVICE_NAME` - name of Andersen charger
* `RENAULT_USERNAME` - login username for Renault API
* `RENAULT_PASSWORD` - login password for Renault API
* `RENAULT_REGISTRATION` - vehicle registration number
