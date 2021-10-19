from pandas import DataFrame, Series, read_csv
import numpy as np


class ADX:

    def __init__(self, data: DataFrame, period: int = 14):
        self.data = data
        self.period = period

        self.t_range = lambda a: np.max([a.h - a.l, np.abs(a.h - a.c), np.abs(a.l - a.c)])
        self.smooth = lambda a: a[a.index[0]] - (a[a.index[0]] / self.period) + a[a.index[1]]
        self.calc_adx = lambda a: (a[a.index[0]] * 13 + a[a.index[1]]) / 14

        self._run()

    def _run(self):
        self.data["tr"] = self.data.apply(self.t_range, axis=1)
        self.data["atr"] = self._atr()
        if len(self.data) >= self.period:
            self._adx_pos()
            self._adx_neg()
            self._adx()

    def rolling(self, a, window):
        shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
        strides = a.strides + (a.strides[-1], )
        return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

    def adx(self):
        try:
            return self.data["adx"]
        except KeyError:
            if len(self.data) >= self.period:
                self.adx_pos()
                self.adx_neg()
                self._adx()
                return self.data["adx"]
            return Series(name="adx")

    def adx_pos(self):
        try:
            return self.data["pdma"]
        except KeyError:
            if len(self.data) >= self.period:
                self._adx_pos()
                return self.data["pdma"]
            else:
                return Series(name="pdma")

    def adx_neg(self):
        try:
            return self.data["ndma"]
        except KeyError:
            if len(self.data) >= self.period:
                self._adx_neg()
                return self.data["ndma"]
            else:
                return Series(name="ndma")

    def _atr(self):
        atr = self.data["tr"].copy()
        n = atr.index[0] + self.period - 1
        fill = np.zeros((self.period, ))
        atr.at[n-1] = atr[:self.period].sum()
        atr = atr.loc[n:].rolling(2).apply(self.smooth).to_numpy()
        return np.append(fill, atr[1:])

    def _adx(self):
        size = len(self.data)
        window = self.period * 2

        dms = self.data[["pdma", "ndma"]].to_numpy()
        diffs = np.diff(dms, axis=1).reshape((size,))
        sums = np.sum(dms, axis=1).reshape((size,))
        s_df = DataFrame(index=self.data.index)
        s_df["diffs"] = diffs
        s_df["sums"] = sums
        divs = s_df[s_df["sums"] > 0].apply(lambda a: np.abs(np.divide(s_df.loc[a.index]["diffs"],
                                                                       s_df.loc[a.index]["sums"])))
        s_df["sums"][s_df["sums"] > 0] = divs["sums"] * 100
        s_df["adx"] = s_df["sums"]
        s_df["adx"].at[window - 1] = np.mean(s_df["adx"][self.period: window])
        s_df["adx"] = s_df["adx"][window:].rolling(2).apply(self.calc_adx)

        self.data["adx"] = s_df["adx"]

    def _dx(self, input_col):
        size = len(self.data)
        # Make an array of pairs containing the high price and 0
        dm = np.zeros((size, 2))
        dm[:, 1] = self.data[input_col].to_numpy().reshape((size,))
        # Find if the current day's high was higher than yesterday's, otherwise 0
        dm = np.max(np.diff(self.rolling(dm, 2), axis=0), axis=2)
        # Fill in first missing item from np.diff
        dm = np.append(np.zeros((1,)), dm)

        # Sum that past period's dm
        dma = DataFrame(dm)
        fill = np.zeros((self.period,))
        dma.at[self.period - 1] = dma[:self.period].sum()
        dma = dma[self.period - 1:].rolling(2).apply(self.smooth)

        dma["atr"] = self.data["atr"]
        divs = dma[dma["atr"] > 0].apply(lambda a: np.divide(a, dma.loc[a.index]["atr"]))[0]
        dma[0][dma["atr"] > 0] = divs
        dma_array = np.append(fill, dma[0][1:])

        return dma_array * 100

    def _adx_pos(self):
        self.data["pdma"] = self._dx("h")

    def _adx_neg(self):
        self.data["ndma"] = self._dx("l")


class SuperTrend:

    def __init__(self, init_data: DataFrame = None, period: int = 9, multiplier: float = 3) -> None:
        self.data = init_data
        self.period = period
        self.mult = multiplier
        self._run()

    def _run(self):
        self._atr()
        self._bands()

    def update_data(self, data: DataFrame) -> None:
        self.data = data

    def _atr(self):
        def true_range(a): return max([a["h"] - a["l"], abs(a["h"] - a["c"]), abs(a["l"] - a["c"])])
        self.data = self.data.assign(tr=self.data.apply(true_range, axis=1))
        self.data = self.data.assign(atr=self.data["tr"]
                                             .rolling(self.period)
                                             .apply(lambda a: (1 / self.period) * a.sum()))

    def _bands(self):
        def u_band(a): return (a["h"] + a["l"]) / 2 + (self.mult * a["atr"])
        def l_band(a): return (a["h"] + a["l"]) / 2 - (self.mult * a["atr"])
        self.data["uband"] = self.data.apply(u_band, axis=1)
        self.data["lband"] = self.data.apply(l_band, axis=1)
        self.data["fuband"] = self.data["uband"]
        self.data["flband"] = self.data["lband"]
        self.data["trend"] = True
        self.data["supertrend"] = np.nan
        for i, frame in self.data[1:].iterrows():
            p = i - 1
            c = i
            # current close > previous final upper band
            if self.data.loc[c]["c"] > self.data.loc[p]["fuband"]:
                self.data.at[c, "trend"] = True
            # current close < previous final lower band
            elif self.data.loc[c]["c"] < self.data.loc[p]["flband"]:
                self.data.at[c, "trend"] = False
            # previous final upper band > current close > previous final lower band
            else:
                self.data.at[c, "trend"] = self.data.loc[p]["trend"]

                # trending AND current final lower band < previous final lower band
                if self.data.loc[c]["trend"] and self.data.loc[c]["flband"] < self.data.loc[p]["flband"]:
                    self.data.at[c, "flband"] = self.data.loc[p]["flband"]
                # not trending AND current final upper band > previous final upper band
                if not self.data.loc[c]["trend"] and self.data.loc[c]["fuband"] > self.data.loc[p]["fuband"]:
                    self.data.at[c, "fuband"] = self.data.loc[p]["fuband"]

            # current price below previous supertrend line
            if self.data.loc[c]["c"] <= self.data.loc[p]["supertrend"]:
                self.data.at[c, "supertrend"] = self.data.loc[c]["fuband"]
            else:
                self.data.at[c, "supertrend"] = self.data.loc[c]["flband"]

    def entries(self):
        d = DataFrame(columns=["Date", "Entry"])
        d["Date"] = self.data["t"]
        d["Entry"] = self.data["c"] > self.data["supertrend"]
        d = d.set_index(d["Date"]).drop("Date", axis=1)
        return d["Entry"]

    def exits(self):
        d = DataFrame(columns=["Date", "Exit"])
        d["Date"] = self.data["t"]
        d["Exit"] = self.data["c"] < self.data["supertrend"]
        d = d.set_index(d["Date"]).drop("Date", axis=1)
        return d["Exit"]

    def bands(self):
        return self.data[["t", "uband", "lband"]]


if __name__ == "__main__":
    df = read_csv("csvs/ETHUSDT_3day_history.csv").drop("Unnamed: 0", axis=1)[:500]
    st = SuperTrend(init_data=df[:150])
    #print(st.bands())
    print(st.entries())
    print(st.exits())

