# stock

Follow instructions at [https://pypi.org/project/telegram-send/]

Build with:
* `docker build . -f Dockerfile.base -t stock_base`
* `docker build . -f Dockerfile.daemon -t stock_daemon`
* `docker build . -f Dockerfile.cron.daily -t stock_daily`
* `docker build . -f Dockerfile.cron.hourly -t stock_hourly`

Run with:
* Background process: `docker run --restart=always --name=stock_daemon -d stock_daemon`

Run `install.sh` to create the cronjobs in the host system, which install:
* Daily cronjob: `docker run --rm --name=stock_daily -d stock_daily`
* Hourly cronjob: `docker run --rm --name=stock_hourly -d stock_hourly`

TODO:
* Use pytz and 'Europe/Madrid' zone to check the current time
