#!/bin/bash
docker stop stock_daemon
docker rm stock_daemon
docker run --restart=unless-stopped --name=stock_daemon -d stock_daemon
