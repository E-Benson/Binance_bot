#import pandas as pd
import os
from os.path import exists
from pandas import DataFrame, Series


class Buffer:

    def __init__(self, save_data=True) -> None:
        self.datasets = dict()
        self.save_data = save_data
        self.size = 200
        self.csv_format = "csvs/{}_{}_candles.csv"
        self.working_candle = dict()
        self.init_directories()

    def __repr__(self) -> str:
        s = "Buffer => "
        for dataset in self.datasets:
            s += f"{dataset} - (size={len(self.datasets[dataset])})\t"
        return s

    def init_directories(self) -> None:
        if not exists("csvs/"):
            os.mkdir("csvs")

    def recv_candle(self, candle: dict) -> None:
        interval = candle["i"]
        print(f"Received {interval} candle")
        # Check if this is a closing candle
        if candle["x"]:
            try:
                df = self.datasets[interval]
            except KeyError:
                cols = list(candle.keys())
                self.datasets[interval] = DataFrame(columns=cols)
            finally:
                candle_series = Series(candle)
                self.datasets[interval] = self.datasets[interval].append(candle_series, ignore_index=True)
                self.working_candle[interval] = None
                # Save the dataframe if save_data is set to True
                if self.save_data:
                    csv_path = self.csv_format.format(candle["s"], interval)
                    self.datasets[interval].append(self.working_candle[interval]).to_csv(csv_path)
        else:
            candle_series = Series(candle)
            self.working_candle[interval] = candle_series

    def get_dataset(self, interval: str, size=None) -> DataFrame:
        size = size if size else self.size
        try:

            df = self.datasets[interval][-size:]
            try:
                wc = self.working_candle[interval]
                return df.append(wc, ignore_index=True)
            except KeyError:
                return df[-size:]
        except KeyError:
            try:
                return DataFrame(self.working_candle[interval], index=self.working_candle[interval].index)
            except KeyError:
                return DataFrame()



