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

        """
        dx = np.abs(np.divide(diffs, sums) * 100)
        tdf = DataFrame(dx)
        tdf.at[window - 1] = np.mean(dx[self.period: window])
        adx = tdf[window:].rolling(2, min_periods=2).apply(lambda a: a[a.index.start] * 13 + a[a.index.start + 1])



        fill = np.zeros((size - adx.shape[0]))
        self.data["adx"] = np.nan_to_num(np.divide(np.append(fill, adx.to_numpy()), 14))
        
        dms = self.data[["pdma", "ndma"]].to_numpy()
        diffs = np.diff(dms, axis=1).reshape((size, ))
        #print(diffs)
        sums = np.sum(dms, axis=1).reshape((size, ))
        #print(self.data["atr"].to_numpy().reshape(size, ))
        #print(dms)
        #print(sums)
        #print(np.nan_to_num(sums, nan=1))
        np.divide(diffs[3:], sums[3:]) * 100
        dx = np.abs(np.divide(diffs, sums) * 100)
        tdf = DataFrame(dx)
        tdf.at[window-1] = np.mean(dx[self.period : window])
        adx = tdf[window:].rolling(2, min_periods=2).apply(lambda a: a[a.index.start] * 13 + a[a.index.start + 1])
        fill = np.zeros((size - adx.shape[0]))
        self.data["adx"] = np.nan_to_num(np.divide(np.append(fill, adx.to_numpy()), 14))
        """

    def _adx_pos(self):
        size = len(self.data)
        # Make an array of pairs containing the high price and 0
        dm = np.zeros((size, 2))
        dm[:, 1] = self.data["h"].to_numpy().reshape((size, ))
        # Find if the current day's high was higher than yesterday's, otherwise 0
        dm = np.max(np.diff(self.rolling(dm, 2), axis=0), axis=2)
        # Fill in first missing item from np.diff
        dm = np.append(np.zeros((1,)), dm)

        # Sum that past period's dm
        dma = DataFrame(dm)
        fill = np.zeros((self.period, ))
        dma.at[self.period-1] = dma[:self.period].sum()
        dma = dma[self.period-1:].rolling(2).apply(self.smooth)

        dma["atr"] = self.data["atr"]
        divs = dma[dma["atr"] > 0].apply(lambda a: np.divide(a, dma.loc[a.index]["atr"]))[0]
        dma[0][dma["atr"] > 0] = divs
        dma_array = np.append(fill, dma[0][1:])


        self.data["pdma"] = dma_array * 100

        """
        dma = np.append(fill, dma[1:])
        print(dma)

        atr = self.data["atr"].to_numpy().reshape(size, )
        fill = np.zeros((atr.shape[0] - dma.shape[0], 1, 1))
        # Divide the sum of past period's dm by avg true range
        filled = np.append(fill, dma)
        #print("dma: ", dma[:20])
        #print(len(dma))
        #print("filled: ", filled[:20])
        nand = np.nan_to_num(filled, nan=1)
        #print("nand: ", nand[:20])
        pdma = np.divide(nand, atr)

        #print(filled[:20])
        #print(pdma[:20])
        self.data["pdma"] = np.nan_to_num(np.divide(np.append(fill, dma), atr))# * 100
        """

    def _adx_neg(self):
        size = len(self.data)
        # Make an array of pairs containing the high price and 0
        dm = np.zeros((size, 2))
        dm[:, 1] = self.data["l"].to_numpy().reshape((size,))
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

        self.data["ndma"] = dma_array * 100
        """
        size = len(self.data)
        dm = np.zeros((size, 2))
        dm[:, 1] = self.data["l"].to_numpy().reshape((size,))
        dm = np.max(np.diff(self.rolling(dm, 2), axis=0), axis=2)
        dma = np.sum(np.lib.stride_tricks.sliding_window_view(dm, (self.period, 1)), axis=2)
        atr = self.data["atr"].to_numpy().reshape(size, )
        fill = np.zeros((atr.shape[0] - dma.shape[0], 1, 1))
        self.data["ndma"] = np.nan_to_num(np.divide(np.append(fill, dma), atr))# * 100
        """



if __name__ == "__main__":
    df = read_csv("csvs/ETHUSDT_3day_history.csv").drop("Unnamed: 0", axis=1)[:500]
    adx = ADX(df, period=5)
    print(adx.adx())
    #print(df)

