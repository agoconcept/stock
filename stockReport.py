#!/usr/bin/python3

# Do not use Xwindows backend
import matplotlib
matplotlib.use('Agg')

# TODO: Temporary hack (see https://stackoverflow.com/a/50970152)
import pandas as pd
pd.core.common.is_list_like = pd.api.types.is_list_like
from alpha_vantage.timeseries import TimeSeries

from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import subprocess
import time
import sys


# Constants
UP_CHAR = u'\u2191'
DN_CHAR = u'\u2193'
EQ_CHAR = u'\u2194'


# Configure Alpha Vantage library
ts = TimeSeries(key='B1R0AXKU3BPVNSO9', output_format='pandas', indexing_type='date')


def getTrendStr(current, average):
    if (current > average):
        return UP_CHAR
    elif (current < average):
        return DN_CHAR
    else:
        return EQ_CHAR


def getStreak(data):
    ret = ""
    for i in range(10):
        if (data[-i-1] > data[-i-2]):
            ret = UP_CHAR + ret
        elif (data[-i-1] < data[-i-2]):
            ret = DN_CHAR + ret
        else:
            ret = EQ_CHAR + ret

    return ret


# Check number of parameters
if len(sys.argv) < 2:
    print("Please specify the ticker to check. Ex: %s '^IBEX'" % (sys.argv[0]))
    sys.exit(1)

# Send initial message to telegram
subprocess.call("telegram-send --format markdown -- '*Collecting and analyzing data for %s...*'" % (sys.argv[1]), shell=True)


# Read data from Yahoo Finance
# NOTE! Retrying, because sometimes it fails
for retry in range(1, 6):
    try:
        stock, meta_data = ts.get_daily_adjusted(sys.argv[1], outputsize='full')
    except:
        print("RETRY #%d - Error reading from Yahoo Finance" % (retry))
        time.sleep(3)
        continue
    break


# Build DataFrame from rolling averages
rolling_5d = pd.DataFrame.rolling(stock['4. close'], 5, min_periods=1).mean()
rolling_20d = pd.DataFrame.rolling(stock['4. close'], 20, min_periods=1).mean()
rolling_60d = pd.DataFrame.rolling(stock['4. close'], 60, min_periods=1).mean()
rolling_250d = pd.DataFrame.rolling(stock['4. close'], 250, min_periods=1).mean()

rolling_5d = stock['4. close'].rolling(5).mean()
rolling_20d = stock['4. close'].rolling(20).mean()
rolling_60d = stock['4. close'].rolling(60).mean()
rolling_250d = stock['4. close'].rolling(250).mean()

rolling_averages = pd.DataFrame({
    '1D (D)': stock['4. close'],
    '5D (W)': rolling_5d,
    '20D (M)': rolling_20d,
    '60D (Q)': rolling_60d,
    '250D (Y)': rolling_250d
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
plt.savefig('stockMax.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
rolling_averages[-750:].plot(**plot_params)
plt.savefig('stock3Y.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
rolling_averages[-250:].plot(**plot_params)
plt.savefig('stock1Y.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
rolling_averages[-60:].plot(**plot_params)
plt.savefig('stock1Q.pdf', dpi=100)
plt.close()


# Calculate MACD for the latest 250 samples
# Adapted from https://www.linkedin.com/pulse/python-tutorial-macd-signal-line-centerline-andrew-hamlet/
stock['26 ema'] = stock['4. close'].ewm(span=26).mean()[-250:]
stock['12 ema'] = stock['4. close'].ewm(span=12).mean()[-250:]
stock['MACD'] = stock['12 ema'] - stock['26 ema']

stock['Signal Line'] = stock['MACD'].ewm(span=9).mean()
stock['MACDh'] = stock['MACD'] - stock['Signal Line']
stock['MACDh_pos'] = np.where(stock['MACDh'] > 0, stock['MACDh'], 0)
stock['MACDh_neg'] = np.where(stock['MACDh'] < 0, stock['MACDh'], 0)
stock['MACDh_delta'] = stock['MACDh'] - stock['MACDh'].shift(1)

stock['Signal Line Crossover'] = np.where(stock['MACD'] > stock['Signal Line'], 1, 0)
stock['Signal Line Crossover'] = np.where(stock['MACD'] < stock['Signal Line'], -1, stock['Signal Line Crossover'])
stock['Centerline Crossover'] = np.where(stock['MACD'] > 0, 1, 0)
stock['Centerline Crossover'] = np.where(stock['MACD'] < 0, -1, stock['Centerline Crossover'])
stock['Buy Sell'] = 2*(np.sign((stock['Signal Line Crossover'] - stock['Signal Line Crossover'].shift(1))[1:]))


# Calculate stochastic indicators
low = stock['4. close'].rolling(5).min()
high = stock['4. close'].rolling(5).max()
stock['stochastic 5'] = 100 * (stock['4. close'][-250:] - low) / (high - low)
stock['stochastic 5 avg'] = stock['stochastic 5'].rolling(5).mean()[-250:]

low = stock['4. close'].rolling(20).min()
high = stock['4. close'].rolling(20).max()
stock['stochastic 20'] = 100 * (stock['4. close'][-250:] - low) / (high - low)
stock['stochastic 20 avg'] = stock['stochastic 20'].rolling(20).mean()[-250:]

low = stock['4. close'].rolling(60).min()
high = stock['4. close'].rolling(60).max()
stock['stochastic 60'] = 100 * (stock['4. close'][-250:] - low) / (high - low)
stock['stochastic 60 avg'] = stock['stochastic 60'].rolling(60).mean()[-250:]


# Calculate delta
stock['delta'] = stock['4. close'] - stock['4. close'].shift(1)


# Calculate RSI
stock['stock_gain'] = np.where(stock['delta'] > 0, stock['delta'], 0)
stock['stock_loss'] = np.where(stock['delta'] < 0, -stock['delta'], 0)

stock['stock_avg_gain'] = stock['stock_gain'].rolling(14).mean()[-250:]
stock['stock_avg_loss'] = stock['stock_loss'].rolling(14).mean()[-250:]

stock['smoothed_RS'] = stock['stock_avg_gain'].rolling(14).mean() / stock['stock_avg_loss'].rolling(14).mean()
stock['RSI'] = 100 - 100 / (1+stock['smoothed_RS'])[-250:]


# Calculate Force Index
stock['force index 2'] = (stock['delta'] * stock['6. volume'] / 1e9).ewm(span=2).mean()[-250:]
stock['force index 13'] = (stock['delta'] * stock['6. volume'] / 1e9).ewm(span=13).mean()[-250:]


# Plot figures
plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['4. close'], title='Close')
plt.grid(linestyle='dotted')
bottom = min(stock['4. close'][-250:])
cur = stock['4. close'][-1]
top = max(stock['4. close'][-250:])
plt.axhline(y=bottom, color='r', linestyle='-')
plt.axhline(y=cur, color='k', linestyle='dotted')
plt.axhline(y=top, color='g', linestyle='-')
plt.savefig('analysis1.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['MACD', 'Signal Line'], title='MACD & Signal Line')
plt.grid(linestyle='dotted')
plt.axhline(y=0.0, color='k', linestyle='-')
# Histogram
bottom = min(stock['MACD'][-250:])*1.3
plt.axhline(y=bottom, color='k', linestyle='-')
plt.bar(x=stock.index[-250:], height=stock['MACDh_neg'][-250:], width=1, bottom=bottom, color='r')
plt.bar(x=stock.index[-250:], height=stock['MACDh_pos'][-250:], width=1, bottom=bottom, color='g')
# Histogram delta
bottom = bottom + min(stock['MACDh'][-250:])*1.3
plt.axhline(y=bottom, color='k', linestyle='-')
plt.bar(x=stock.index[-250:], height=2*stock['MACDh_delta'][-250:], width=1, bottom=bottom, color='b')
plt.savefig('analysis2.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['Centerline Crossover', 'Buy Sell'], title='Signal Line & Centerline Crossovers', ylim=(-3,3))
plt.grid(linestyle='dotted')
plt.savefig('analysis3.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['stochastic 5 avg'], title='Stochastic 5 days', ylim=(-20,120))
plt.grid(linestyle='dotted')
plt.axhline(y=0.0, color='k', linestyle='-')
plt.axhline(y=20.0, color='g', linestyle='dotted')
plt.axhline(y=80.0, color='r', linestyle='dotted')
plt.axhline(y=100.0, color='k', linestyle='-')
plt.savefig('analysis4.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['stochastic 20 avg'], title='Stochastic 20 days', ylim=(-20,120))
plt.grid(linestyle='dotted')
plt.axhline(y=0.0, color='k', linestyle='-')
plt.axhline(y=20.0, color='g', linestyle='dotted')
plt.axhline(y=80.0, color='r', linestyle='dotted')
plt.axhline(y=100.0, color='k', linestyle='-')
plt.savefig('analysis5.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['stochastic 60 avg'], title='Stochastic 60 days', ylim=(-20,120))
plt.grid(linestyle='dotted')
plt.axhline(y=0.0, color='k', linestyle='-')
plt.axhline(y=20.0, color='g', linestyle='dotted')
plt.axhline(y=80.0, color='r', linestyle='dotted')
plt.axhline(y=100.0, color='k', linestyle='-')
plt.savefig('analysis6.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['RSI'], title='RSI', ylim=(-20,120))
plt.grid(linestyle='dotted')
plt.axhline(y=0.0, color='k', linestyle='-')
plt.axhline(y=30.0, color='g', linestyle='dotted')
plt.axhline(y=70.0, color='r', linestyle='dotted')
plt.axhline(y=100.0, color='k', linestyle='-')
plt.savefig('analysis7.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['force index 2', 'force index 13'], title='Force index')
plt.grid(linestyle='dotted')
plt.savefig('analysis8.pdf', dpi=100)
plt.close()

subprocess.call("pdfunite analysis?.pdf analysis.pdf", shell=True)


# Prepare report
formatted_date = stock.index[-1:][0]

prev_close = stock['4. close'][-2]
last_close = stock['4. close'][-1]
diff_abs = last_close-prev_close
diff_pct = 100.0 * (last_close-prev_close) / prev_close

open_val = stock['1. open'][-1]
high_val = stock['2. high'][-1]
low_val = stock['3. low'][-1]
vol_val = stock['6. volume'][-1]

trend5d = getTrendStr(last_close, rolling_5d[-1])
trend20d = getTrendStr(last_close, rolling_20d[-1])
trend60d = getTrendStr(last_close, rolling_60d[-1])
trend250d = getTrendStr(last_close, rolling_250d[-1])

min5d = min(stock['3. low'][-5:])
max5d = max(stock['2. high'][-5:])
perc5d = 100.0 * (last_close - min5d) / (max5d - min5d)

min20d = min(stock['3. low'][-20:])
max20d = max(stock['2. high'][-20:])
perc20d = 100.0 * (last_close - min20d) / (max20d - min20d)

min60d = min(stock['3. low'][-60:])
max60d = max(stock['2. high'][-60:])
perc60d = 100.0 * (last_close - min60d) / (max60d - min60d)

min250d = min(stock['3. low'][-250:])
max250d = max(stock['2. high'][-250:])
perc250d = 100.0 * (last_close - min250d) / (max250d - min250d)

streak = getStreak(stock['4. close'])

info = """
********************
ANALYSIS: %s
********************
Current: %.2f
Diff: %+.2f (%+.2f%%)
Pre: %.2f - Op: %.2f
Range: %.2f - %.2f
Volume: %.3fB
---
5d avg: %.2f (%s)
20d avg: %.2f (%s)
60d avg: %.2f (%s)
250d avg: %.2f (%s)
---
5d range: %.2f - %.2f (%.2f%%)
20d range: %.2f - %.2f (%.2f%%)
60d range: %.2f - %.2f (%.2f%%)
250d range: %.2f - %.2f (%.2f%%)
---
10 day streak: %s
""" % (
        formatted_date,
        last_close,
        diff_abs, diff_pct,
        prev_close, open_val,
        low_val, high_val,
        vol_val/1000000.0,
        rolling_5d[-1], trend5d,
        rolling_20d[-1], trend20d,
        rolling_60d[-1], trend60d,
        rolling_250d[-1], trend250d,
        min5d, max5d, perc5d,
        min20d, max20d, perc20d,
        min60d, max60d, perc60d,
        min250d, max250d, perc250d,
        streak
        )


# Send data to telegram
subprocess.call("telegram-send -- '%s'" % (info), shell=True)

subprocess.call("telegram-send -f stockMax.pdf stock3Y.pdf stock1Y.pdf stock1Q.pdf analysis.pdf", shell=True)

# Clean up
subprocess.call("rm stockMax.pdf stock3Y.pdf stock1Y.pdf stock1Q.pdf analysis*.pdf", shell=True)
