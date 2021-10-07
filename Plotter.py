import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.animation as ani
from matplotlib import style
from matplotlib.gridspec import GridSpec
import datetime
from dateutil import tz
import pandas as pd
from Strategy import EMATrader, MACDTrader
#from ta.trend import EMAIndicator, MACD

style.use("ggplot")

func = lambda x: datetime.datetime.utcfromtimestamp(x // 1000)
data_csv_path1 = "csvs/ETHUSDT_1m_candles.csv"
data_csv_path2 = "csvs/ETHUSDT_5m_candles.csv"
trade_csv_path = "csvs/bot_tr.csv"

fig = plt.figure()
gs = GridSpec(6, 4, figure=fig)

ax = fig.add_subplot(gs[:2, :])
ax2 = fig.add_subplot(gs[2, :])
ax3 = fig.add_subplot(gs[3:5, :])
ax4 = fig.add_subplot(gs[5, :])
ax2.axes.xaxis.set_visible(False)
ax2.axes.yaxis.set_visible(False)
ax4.axes.xaxis.set_visible(False)
ax4.axes.yaxis.set_visible(False)


from_tz = tz.tzutc()
to_tz = tz.tzlocal()


def form_time(_time):
    _time = _time / 1000
    utc_time = datetime.datetime.utcfromtimestamp(_time)
    utc_time = utc_time.replace(tzinfo=from_tz)
    return utc_time.astimezone(to_tz)


def plot_candles(axis, df):
    for i, row in df.iterrows():
        if row["v"]:
            clr = "r" if row["o"] > row["c"] else "g"
            axis.plot([row["t"], row["t"]], [row["l"], row["h"]], color=clr, linewidth=1, zorder=1)
            axis.plot([row["t"], row["t"]], [row["o"], row["c"]], color=clr, linewidth=2.25, zorder=1)
        else:
            axis.plot(row["t"], row["c"], marker="o", color="k", markersize=3)


def plot_with_ema(axis, df):
    df["t"] = df["t"].apply(form_time)
    plot_ema(axis, df, show_positions=True, show_highlight=True)
    plot_candles(axis, df)


def plot_ema(axis, df, window=9, color="#2b74c2", show_positions=False, show_highlight=False):
    emat = EMATrader(df, period=window)

    axis.plot(df["t"], emat.emas, linewidth=1.5, zorder=2, alpha=0.4, color=color)
    if show_highlight:
        plot_signals(axis, emat)
    if show_positions:
        plot_positions(axis, emat)


def plot_macd(axis, df, show=True, show_positions=False, show_highlight=False):
    macdi =  MACDTrader(df)
    macd = macdi.macdis
    macdd = macdi.macdds
    macds = macdi.macdss
    if show:
        axis.plot(df["t"], macd, color="r")
        axis.plot(df["t"], macds, color="k")
        for i, row in df.iterrows():
            axis.plot([df["t"].iloc[i], df["t"].iloc[i]], [0, macdd.iloc[i]], color="#2b74c2", alpha=0.2)
    if show_positions:
        plot_positions(axis, macdi)
    if show_highlight:
        plot_signals(axis, macdi)


def plot_positions(axis, strategy):
    positions = strategy.test_strategy()
    for position in positions:
        axis.plot(position.buy_time, position.buy_price, marker="^", markersize=7, color="g")
        axis.plot(position.sell_time, position.sell_price, marker="v", markersize=7, color="r")


def plot_signals(axis, strategy):
    signals = strategy.test_strategy(signals=True)
    spans = get_spans(strategy.data, signals)
    for s, e in spans:
        axis.axvspan(s, e, color='g', alpha=0.07)


def get_spans(df, signals):
    s = None
    spans = list()
    for i, row in df.iterrows():
        if signals[i]:
            if s:
                spans.append((s, row["t"]))
                s = None
            else:
                s = row["t"]
    return spans


def plot_trades(axis, df):
    trades = df
    trades["buy_time"] = trades["buy_time"].apply(form_time)
    trades["sell_time"] = trades["sell_time"].apply(form_time)
    if trades.size > 0:
        for i in trades.index:
            trade = trades.iloc[i]
            bp = trade["buy_price"]
            bd = trade["buy_time"]
            sp = trade["sell_price"]
            sd = trade["sell_time"]
            clr = "r" if sp-bp < 0 else "g"
            axis.plot([bd, sd], [bp, sp], color=clr, linewidth=1, zorder=3)
            axis.plot(bd, bp, "k^", label=sp-bp, markersize=4, zorder=5)
            axis.plot(sd, sp, "kv", label=sp, markersize=4, zorder=6)


def update(_):
    df_1m = pd.read_csv(data_csv_path1)
    df_1m["t"] = df_1m["t"].apply(form_time)
    df_5m = pd.read_csv(data_csv_path2)
    df_5m["t"] = df_5m["t"].apply(form_time)

    ax.clear()
    ax2.clear()
    ax3.clear()
    ax4.clear()

    ax.axes.yaxis.set_major_formatter(ticker.FormatStrFormatter('$%.2f'))
    ax3.axes.yaxis.set_major_formatter(ticker.FormatStrFormatter('$%.2f'))
    ax.axes.set_title("ETH/USDT 1m Candles")
    ax3.axes.set_title("ETH/USDT 5m Candles")

    plot_candles(ax, df_1m)
    plot_ema(ax, df_1m)
    plot_macd(ax2, df_1m, show_highlight=True)

    plot_candles(ax3, df_5m)
    plot_ema(ax3, df_5m)
    plot_macd(ax4, df_5m, show_highlight=True)


a = ani.FuncAnimation(fig, update, interval=1000)
plt.show()
