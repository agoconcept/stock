#!/bin/bash
docker build . -f Dockerfile.base -t stock_base
docker build . -f Dockerfile.daemon -t stock_daemon
docker build . -f Dockerfile.cron.daily -t stock_daily
docker build . -f Dockerfile.cron.hourly -t stock_hourly
