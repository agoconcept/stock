#!/usr/bin/python3

# Do not use Xwindows backend
import matplotlib
matplotlib.use('Agg')

import pandas as pd
from pandas_datareader import DataReader
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import cm
import subprocess


def getTrendStr(current, average):
    if (current > average):
        return u'\u2191'
    elif (current < average):
        return u'\u2193'
    else:
        return u'\u2194'


# Read IBEX data from Yahoo Finance
# NOTE! Retrying, because sometimes it fails
for retry in range(1, 6):
    try:
        stock = DataReader('^IBEX',  'yahoo', datetime(2005, 1, 1), datetime.today())
    except:
        print("RETRY #%d - Error reading from Yahoo Finance" % (retry))
        continue
    break


# Build DataFrame from rolling averages
rolling_5d = pd.rolling_mean(stock['Adj Close'], 5, min_periods=1)
rolling_20d = pd.rolling_mean(stock['Adj Close'], 20, min_periods=1)
rolling_60d = pd.rolling_mean(stock['Adj Close'], 60, min_periods=1)
rolling_250d = pd.rolling_mean(stock['Adj Close'], 250, min_periods=1)

rolling_averages = pd.DataFrame({
    '1D (D)': stock['Adj Close'][:-2],
    '5D (W)': rolling_5d[:-2],
    '20D (M)': rolling_20d[:-2],
    '60D (Q)': rolling_60d[:-2],
    '250D (Y)': rolling_250d[:-2]
    },
    columns=['1D (D)', '5D (W)', '20D (M)', '60D (Q)', '250D (Y)'])

# Generate figures
plot_params = {
    'title': 'Rolling averages',
    'linewidth': 2,
    'solid_capstyle': 'round',
    'grid': True,
    'fontsize': 8,
    'colormap': cm.gist_rainbow
}

plt.figure(figsize=(32, 24), dpi=100)
rolling_averages.plot(**plot_params)
plt.savefig('image1.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
rolling_averages[-250:].plot(**plot_params)
plt.savefig('image2.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
rolling_averages[-60:].plot(**plot_params)
plt.savefig('image3.pdf', dpi=100)
plt.close()


# Send info to telegram bot
formatted_date = datetime.today().strftime("%Y-%m-%d")
subprocess.call("telegram-send -- '*********'", shell=True)
subprocess.call("telegram-send -- 'ANALYSIS: %s'" % (formatted_date), shell=True)


prev_close = stock['Adj Close'][-3]
last_close = stock['Adj Close'][-2]
diff_abs = last_close-prev_close
diff_pct = 100.0 * (last_close-prev_close) / prev_close

subprocess.call("telegram-send -- 'Close: %.2f'" % (last_close), shell=True)
if (diff_abs > 0.0):
    subprocess.call("telegram-send -- 'Diff: +%.2f (+%.2f%%)'" % (diff_abs, diff_pct), shell=True)
else:
    subprocess.call("telegram-send -- 'Diff: %.2f (%.2f%%)'" % (diff_abs, diff_pct), shell=True)

open_val = stock['Open'][-2]
high_val = stock['High'][-2]
low_val = stock['Low'][-2]
vol_val = stock['Volume'][-2]

subprocess.call("telegram-send -- 'Op: %.2f'" % (open_val), shell=True)
subprocess.call("telegram-send -- 'Hi: %.2f'" % (high_val), shell=True)
subprocess.call("telegram-send -- 'Lo: %.2f'" % (low_val), shell=True)
subprocess.call("telegram-send -- 'Volume: %.1f'" % (vol_val), shell=True)

subprocess.call("telegram-send -- '---'" % (last_close), shell=True)

trend = getTrendStr(last_close, rolling_5d[-2])
subprocess.call("telegram-send -- '5d avg: %.2f (%s)'" % (rolling_5d[-2], trend), shell=True)

trend = getTrendStr(last_close, rolling_20d[-2])
subprocess.call("telegram-send -- '20d avg: %.2f (%s)'" % (rolling_20d[-2], trend), shell=True)

trend = getTrendStr(last_close, rolling_60d[-2])
subprocess.call("telegram-send -- '60d avg: %.2f (%s)'" % (rolling_60d[-2], trend), shell=True)

trend = getTrendStr(last_close, rolling_250d[-2])
subprocess.call("telegram-send -- '250d avg: %.2f (%s)'" % (rolling_250d[-2], trend), shell=True)

subprocess.call("telegram-send -- '---'" % (last_close), shell=True)

subprocess.call("telegram-send -f image1.pdf image2.pdf image3.pdf", shell=True)

subprocess.call("rm image1.pdf image2.pdf image3.pdf", shell=True)
