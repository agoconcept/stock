# stock

There's no need to setup telegram-send, as it is already configured in the docker
images. Anyway, the instructions if needed are available at
[https://pypi.org/project/telegram-send/]

Build with `./build.sh`, which executes:
* `docker build . -f Dockerfile.base -t stock_base`
* `docker build . -f Dockerfile.daemon -t stock_daemon`
* `docker build . -f Dockerfile.cron.daily -t stock_daily`
* `docker build . -f Dockerfile.cron.hourly -t stock_hourly`

**NOTE!!!** It may be needed to avoid the Docker cache by adding the `--no-cache` parameter to `docker build`

Run `sudo ./install.sh` to create the cronjobs in the host system, which install:
* Daily cronjob: `docker run --rm --name=stock_daily -d stock_daily`
* Hourly cronjob: `docker run --rm --name=stock_hourly -d stock_hourly`

Run with `./run.sh`, which stops previous containers and runs:
* Background process: `docker run --restart=unless-stopped --name=stock_daemon -d stock_daemon`

## Telegram commands

* Send `/setcommands` to @BotFather
* Select `@santibexbot` to set the commands for this bot
* Send the following list of commands:
```
ibex - Send ^IBEX report
ericsson - Send STO:ERIC-B report
df - Send MDF.MC report
tef - Send TEF.MC report
dowjones - Send ^DJI report
nasdaq - Send NASDAQ:^IXIC report
```
* Enjoy :)

## Query test for a stock
You can easily test query a stock with the following commands:
```
SYMBOL=
TOKEN=$(cat token.alpha_vantage)
curl "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=${SYMBOL}&apikey=${TOKEN}"
```

