import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.animation as ani
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import datetime as dt
from dateutil import tz
import pandas as pd
from pandas.errors import EmptyDataError
from Strategy import EMATrader
from StateStrategy import ADXStateTrader
from Indicators import SuperTrend
import BinanceInterface as bi

symbol = "ETH"
plt.style.use('ggplot')
chart_size = 200

data_csv_path1 = f"csvs/{symbol}USDT_1m_candles.csv"
data_csv_path2 = f"csvs/{symbol}USDT_5m_candles.csv"
trade_csv_path = f"csvs/{symbol}_trades.csv"

from_tz = tz.tzutc()
to_tz = tz.tzlocal()

window = 5


def form_time(_time):
    _time = _time / 1000
    utc_time = dt.datetime.utcfromtimestamp(_time)
    utc_time = utc_time.replace(tzinfo=from_tz)
    return utc_time.astimezone(to_tz)


def make_figure():
    fig, frame1_0 = plt.subplots()
    frame1_1 = frame1_0.twinx()
    return frame1_0, frame1_1


def get_data(fname):
    df = pd.read_csv(fname)
    df = df.drop(["Unnamed: 0"], axis=1)
    df["t"] = df["t"].apply(form_time)
    return df[-chart_size:].dropna()


def plot_candles(axis, df):
    for i, row in df.iterrows():
        if row["v"]:
            clr = "r" if row["o"] > row["c"] else "g"
            axis.plot([row["t"], row["t"]], [row["l"], row["h"]], color=clr, linewidth=1, zorder=2)
            axis.plot([row["t"], row["t"]], [row["o"], row["c"]], color=clr, linewidth=2.25, zorder=2)
        else:
            axis.plot(row["t"], row["c"], marker="o", color="k", markersize=3)


def plot_adx(axis1, df):
    adx = ADXStateTrader(window=window, threshold=20)
    if len(df) >= window:
        adx.update_data(df)
        _adx = adx.ind.adx()
        _adxp = adx.ind.adx_pos()
        _adxn = adx.ind.adx_neg()
        #axis1.plot(df["t"], _adx, color="#cccccc", alpha=0.1, zorder=2, linewidth=3)
        axis1.plot(df["t"], _adxp, color="b", alpha=0.2, zorder=3, linewidth=3)
        axis1.plot(df["t"], _adxn, color="r", alpha=0.2, zorder=3, linewidth=3)
        axis1.grid(b=False)
        axis1.axis("off")


def plot_ema(axis, df, window=9, color="#2b74c2"):
    emat = EMATrader(df, period=window)
    axis.plot(df["t"], emat.emas, linewidth=1.5, zorder=2, alpha=0.4, color=color)


def get_trades(oldest):
    df = pd.read_csv(f"csvs/{symbol}_trades.csv")
    df["bt"] = df["bt"].apply(form_time)
    #print(df)
    return df[df["bt"] >= oldest]


def plot_trades(axis, df):
    if df.size:
        for i in df.index:
            trade = df.loc[i]
            bp = trade["b"]
            bd = trade["bt"]
            sp = trade["s"]
            sd = trade["st"]
            clr = "r" if sp-bp < 0 else "g"
            axis.plot([bd, sd], [bp, sp], color=clr, linewidth=3, zorder=3)
            axis.plot(bd, bp, "k^", label=sp-bp, markersize=4, zorder=5)
            axis.plot(sd, sp, "kv", label=sp, markersize=4, zorder=6)


def plot_super_trend(axis, df, period=5, multiplier=3):
    st = SuperTrend(init_data=df, period=period, multiplier=multiplier)
    data = st.data
    axis.plot(data["t"], data["fuband"], color="c", alpha=0.1, zorder=3)
    #axis.plot(data["t"], data["uband"], color="b", alpha=0.5)
    axis.plot(data["t"], data["flband"], color="c", alpha=0.1, zorder=3)
    #axis.plot(data["t"], data["lband"], color="w", alpha=0.1, zorder=3)
    #print(data)
    p_clr = "r"
    position_value = 0
    position_date = None
    for i in range(len(data[period:])):
        clr = "g" if data.iloc[i]["c"] > data.iloc[i]["supertrend"] else "r"
        # Add buy-in and sell-out markers
        if clr != p_clr:
            marker = "^" if clr == "g" else "v"
            diff = data.iloc[i]["flband"] - data.iloc[i]["c"] if clr == "g" else data.iloc[i]["fuband"] - data.iloc[i]["c"]
            axis.plot(data.iloc[i]["t"], data.iloc[i]["c"], marker=marker, color=clr, markersize=5)
            axis.plot(data.iloc[i]["t"], data.iloc[i]["c"] + (diff / 2), marker=marker, color=clr, markersize=5)
            axis.plot(data.iloc[i]["t"], data.iloc[i]["supertrend"], marker=marker, color=clr, markersize=5)
            # highlight background for each position
            if clr == "r":
                shade = "r" if position_value > data.iloc[i]["c"] else "g"
                axis.axvspan(position_date, data.iloc[i]["t"], facecolor=shade, alpha=0.1)
            position_value = data.iloc[i]["c"]
            position_date = data.iloc[i]["t"]
        # Add a line tracking the buy-in price
        if clr == "g":
            axis.plot(data.iloc[i]["t"], position_value, marker="o", color="c", alpha=0.2, markersize=2)
        # Plot supertrend line
        axis.plot([df.iloc[i]["t"], df.iloc[i+1]["t"]],
                  [data.iloc[i]["supertrend"], data.iloc[i+1]["supertrend"]],
                  color=clr, alpha=0.4, zorder=4)
        p_clr = clr



def func(num_data):
    _cols = 2
    _rows = 3
    _axes = list()
    _fig = plt.figure()
    gs = GridSpec(_rows * num_data, _cols * num_data, figure=_fig)
    for i in range(num_data):
        a = 2 * (i + 1) - 1 if i else 2 * i
        b = 2 * (i + 1) + 1 if i else 2 * (i + 1)
        main_ax = _fig.add_subplot(gs[a:b, :])
        main_ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
        main_ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('$%.7f'))
        a = 2 * (i + 1) + 1 if i else 2 * (i + 1)
        sub_ax = _fig.add_subplot(gs[a, :])
        sub_ax.axes.xaxis.set_visible(False)
        sub_ax.axes.yaxis.set_visible(False)

        _axes.append((main_ax, sub_ax))
    return _fig, _axes


def animate(_):
    try:
        df_1m = get_data(data_csv_path1)
        df_5m = get_data(data_csv_path2)
        dfs = [df_1m, df_5m]
        trades = get_trades(df_1m["t"].iloc[0])
        #print(trades)
    except EmptyDataError:
        print("File currently being written to...")
        return

    for (m_ax, s_ax), df in zip(axes, dfs):
        m_ax.clear()
        s_ax.clear()

        m_ax.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M:%p'))
        m_ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('$%.7f'))

        plot_candles(m_ax, df)
        plot_super_trend(m_ax, df, period=3)
        #plot_ema(m_ax, df)
        #plot_trades(m_ax, trades)

        plot_adx(s_ax, df)


if __name__ == "__main__":
    from_disk = False
    if from_disk:
        fig, axes = func(2)

        animate(1)
        a = ani.FuncAnimation(fig, animate, interval=10000)
        plt.show()
    else:
        df = bi.get_historical_data("SHIBUSDT", candle_size="1m", time_frame="6 hour")
        fig = plt.figure()
        ax = fig.add_subplot()
        plot_candles(ax, df)
        plot_super_trend(ax, df, period=10, multiplier=3)
        plt.show()






