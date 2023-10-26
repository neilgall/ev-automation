FROM python:3.11.6-slim-bullseye AS build

WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY . .
ENTRYPOINT ["python", "main.py"]
