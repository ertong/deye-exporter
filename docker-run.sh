#!/bin/bash
DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"

./docker-stop.sh

touch config.yml

docker run -d \
    --restart unless-stopped \
    -p 23790:9090 \
    -v $DIR/config.yml:/app/config.yml \
    --log-driver json-file --log-opt max-size=100m \
    --name deye_exporter \
    ertong/deye-exporter
