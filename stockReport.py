#!/usr/bin/python3

# Do not use Xwindows backend
import matplotlib
matplotlib.use('Agg')

import pandas as pd
from pandas_datareader import DataReader
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
subprocess.call("telegram-send -- 'Collecting and analyzing data for %s...'" % (sys.argv[1]), shell=True)


# Read IBEX data from Yahoo Finance
# NOTE! Retrying, because sometimes it fails
for retry in range(1, 6):
    try:
        stock = DataReader(sys.argv[1],  'yahoo', datetime(2005, 1, 1), datetime.today(), retry_count=10)
    except:
        print("RETRY #%d - Error reading from Yahoo Finance" % (retry))
        time.sleep(3)
        continue
    break


# Build DataFrame from rolling averages
rolling_5d = pd.rolling_mean(stock['Adj Close'], 5, min_periods=1)
rolling_20d = pd.rolling_mean(stock['Adj Close'], 20, min_periods=1)
rolling_60d = pd.rolling_mean(stock['Adj Close'], 60, min_periods=1)
rolling_250d = pd.rolling_mean(stock['Adj Close'], 250, min_periods=1)

rolling_averages = pd.DataFrame({
    '1D (D)': stock['Adj Close'],
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
stock['26 ema'] = pd.ewma(stock['Adj Close'], span=26)[-250:]
stock['12 ema'] = pd.ewma(stock['Adj Close'], span=12)[-250:]
stock['MACD'] = stock['12 ema'] - stock['26 ema']

stock['Signal Line'] = pd.ewma(stock['MACD'], span=9)
stock['MACDh'] = stock['MACD'] - stock['Signal Line']
stock['MACDh_pos'] = np.where(stock['MACDh'] > 0, stock['MACDh'], 0)
stock['MACDh_neg'] = np.where(stock['MACDh'] < 0, stock['MACDh'], 0)

stock['Signal Line Crossover'] = np.where(stock['MACD'] > stock['Signal Line'], 1, 0)
stock['Signal Line Crossover'] = np.where(stock['MACD'] < stock['Signal Line'], -1, stock['Signal Line Crossover'])
stock['Centerline Crossover'] = np.where(stock['MACD'] > 0, 1, 0)
stock['Centerline Crossover'] = np.where(stock['MACD'] < 0, -1, stock['Centerline Crossover'])
stock['Buy Sell'] = (2*(np.sign(stock['Signal Line Crossover'] - stock['Signal Line Crossover'].shift(1))))


# Calculate stochastic indicator
low = pd.rolling_min(stock['Adj Close'], 5)
high = pd.rolling_max(stock['Adj Close'], 5)
stock['stochastic 5'] = 100 * (stock['Adj Close'][-250:] - low) / (high - low)
stock['stochastic 5 avg'] = pd.rolling_mean(stock['stochastic 5'], 5, min_periods=1)[-250:]

low = pd.rolling_min(stock['Adj Close'], 20)
high = pd.rolling_max(stock['Adj Close'], 20)
stock['stochastic 20'] = 100 * (stock['Adj Close'][-250:] - low) / (high - low)
stock['stochastic 20 avg'] = pd.rolling_mean(stock['stochastic 20'], 5, min_periods=1)[-250:]


# Calculate delta
stock['delta'] = stock['Adj Close'] - stock['Adj Close'].shift(1)


# Calculate RSI
stock['stock_gain'] = np.where(stock['delta'] > 0, stock['delta'], 0)
stock['stock_loss'] = np.where(stock['delta'] < 0, -stock['delta'], 0)

stock['stock_avg_gain'] = pd.rolling_mean(stock['stock_gain'], 14, min_periods=1)[-250:]
stock['stock_avg_loss'] = pd.rolling_mean(stock['stock_loss'], 14, min_periods=1)[-250:]

stock['smoothed_RS'] = pd.rolling_mean(stock['stock_avg_gain'], 14, min_periods=1) / pd.rolling_mean(stock['stock_avg_loss'], 14, min_periods=1)
stock['RSI'] = 100 - 100 / (1+stock['smoothed_RS'])[-250:]


# Calculate Force Index
stock['force index 2'] = pd.ewma(stock['delta'] * stock['Volume'] / 1e9, span=2)[-250:]
stock['force index 13'] = pd.ewma(stock['delta'] * stock['Volume'] / 1e9, span=13)[-250:]


# Plot figures
plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['Adj Close'], title='Close')
plt.grid(linestyle='dotted')
bottom = min(stock['Adj Close'][-250:])
cur = stock['Adj Close'][-1]
top = max(stock['Adj Close'][-250:])
plt.axhline(y=bottom, color='r', linestyle='-')
plt.axhline(y=cur, color='k', linestyle='dotted')
plt.axhline(y=top, color='g', linestyle='-')
plt.savefig('analysis1.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['MACD', 'Signal Line'], title='MACD & Signal Line')
plt.grid(linestyle='dotted')
plt.axhline(y=0.0, color='k', linestyle='-')
bottom = min(stock['MACD'][-250:])*1.5
plt.axhline(y=bottom, color='k', linestyle='-')
plt.bar(x=stock.index[-250:], height=stock['MACDh_neg'][-250:], width=1, bottom=bottom, color='r')
plt.bar(x=stock.index[-250:], height=stock['MACDh_pos'][-250:], width=1, bottom=bottom, color='g')
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
stock[-250:].plot(y=['RSI'], title='RSI', ylim=(-20,120))
plt.grid(linestyle='dotted')
plt.axhline(y=0.0, color='k', linestyle='-')
plt.axhline(y=30.0, color='g', linestyle='dotted')
plt.axhline(y=70.0, color='r', linestyle='dotted')
plt.axhline(y=100.0, color='k', linestyle='-')
plt.savefig('analysis6.pdf', dpi=100)
plt.close()

plt.figure(figsize=(32, 24), dpi=100)
stock[-250:].plot(y=['force index 2', 'force index 13'], title='Force index')
plt.grid(linestyle='dotted')
plt.savefig('analysis7.pdf', dpi=100)
plt.close()

subprocess.call("pdfunite analysis?.pdf analysis.pdf", shell=True)


# Prepare report
formatted_date = stock.index[-1:][0].strftime("%Y-%m-%d")

prev_close = stock['Adj Close'][-2]
last_close = stock['Adj Close'][-1]
diff_abs = last_close-prev_close
diff_pct = 100.0 * (last_close-prev_close) / prev_close

open_val = stock['Open'][-1]
high_val = stock['High'][-1]
low_val = stock['Low'][-1]
vol_val = stock['Volume'][-1]

trend5d = getTrendStr(last_close, rolling_5d[-1])
trend20d = getTrendStr(last_close, rolling_20d[-1])
trend60d = getTrendStr(last_close, rolling_60d[-1])
trend250d = getTrendStr(last_close, rolling_250d[-1])

min5d = min(stock['Low'][-5:])
max5d = max(stock['High'][-5:])
perc5d = 100.0 * (last_close - min5d) / (max5d - min5d)

min20d = min(stock['Low'][-20:])
max20d = max(stock['High'][-20:])
perc20d = 100.0 * (last_close - min20d) / (max20d - min20d)

min60d = min(stock['Low'][-60:])
max60d = max(stock['High'][-60:])
perc60d = 100.0 * (last_close - min60d) / (max60d - min60d)

min250d = min(stock['Low'][-250:])
max250d = max(stock['High'][-250:])
perc250d = 100.0 * (last_close - min250d) / (max250d - min250d)

streak = getStreak(stock['Adj Close'])

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
