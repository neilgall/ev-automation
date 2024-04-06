#!/bin/bash
source .env

docker stop ev-automation
docker rm ev-automation

docker build -t ev-automation .

docker run \
    --name ev-automation \
    --restart always \
    --detach \
    -e ANDERSEN_USERNAME="$ANDERSEN_USERNAME" \
    -e ANDERSEN_PASSWORD="$ANDERSEN_PASSWORD" \
    -e ANDERSEN_DEVICE_NAME="$ANDERSEN_DEVICE_NAME" \
    -e RENAULT_USERNAME="$RENAULT_USERNAME" \
    -e RENAULT_PASSWORD="$RENAULT_PASSWORD" \
    -e RENAULT_REGISTRATION="$RENAULT_REGISTRATION" \
    -e AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
    -e AWS_DEFAULT_REGION=eu-west-1 \
    -v /etc/localtime:/etc/localtime:ro \
    ev-automation