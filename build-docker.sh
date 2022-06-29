#!/bin/bash

docker image rm localhost/trader
docker build --rm -t localhost/trader .
docker run --name test -it localhost/trader
