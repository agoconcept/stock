#!/usr/bin/python3

from pandas_datareader import DataReader
from datetime import datetime, date, time, timedelta
import subprocess
from time import sleep

THRESHOLD = 1.0     # Percentage

# Only execute between 9:00 and 18:00
if not datetime.now().hour in range(9, 18):
    exit(1)

# Read IBEX data from Yahoo Finance
# NOTE! Retrying, because sometimes it fails
for retry in range(1, 6):
    try:
        stock = DataReader('^IBEX',  'yahoo', date.today()-timedelta(days=1), date.today(), retry_count=10)
    except:
        print("RETRY #%d - Error reading from Yahoo Finance" % (retry))
        sleep(3)
        continue
    break


# Check if change is over a threshold compared to previous day
curr_val = stock['Close'][1]
prev_val = stock['Close'][0]
delta = curr_val - prev_val
perc_var = 100.0 * delta / prev_val

if abs(perc_var) >= THRESHOLD:

    # Send message
    subprocess.call("telegram-send -- 'NOTE!!!'", shell=True)
    subprocess.call("telegram-send -- 'Current: %.2f'" % (curr_val), shell=True)

    if delta > 0.0:
        subprocess.call("telegram-send -- '+%.2f (+%.2f%%)'" % (delta, perc_var), shell=True)
    else:
        subprocess.call("telegram-send -- '%.2f (%.2f%%)'" % (delta, perc_var), shell=True)

