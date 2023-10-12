FROM python:3.11.6-slim-bullseye AS build

WORKDIR /app
COPY requirements.txt /app
RUN python -m venv .venv
RUN .venv/bin/pip install -r requirements.txt

FROM python:3.11.6-slim-bullseye AS final
COPY --from=build /app/.venv /app/.venv
COPY controller /app/controller
COPY model /app/model
COPY services /app/services
COPY schedule.py /app

WORKDIR /app
RUN ls -al /app
ENTRYPOINT [".venv/bin/python", "schedule.py"]
