from os import mkdir
from os.path import exists
from pandas import DataFrame, Series


class Buffer:

    def __init__(self, init_data=None, save_data=True) -> None:
        self.datasets = init_data if init_data is not None else dict()
        self.save_data = save_data
        self.size = 200
        self.csv_format = "csvs/{}_{}_candles.csv"
        self.working_candle = dict()
        self.init_directories()

    #
    # Print out information about all of the datasets
    #
    def __repr__(self) -> str:
        s = "Buffer => "
        for dataset in self.datasets:
            # Print the interval and the size of its dataset
            s += f"{dataset} - (size={len(self.datasets[dataset])})\t"
        return s

    #
    # Check to ensure the required directories exist
    #
    def init_directories(self) -> None:
        if not exists("csvs/"):
            mkdir("csvs")
    #
    # Adds a candle from the websocket listener to the correct dataset
    #
    def recv_candle(self, candle: dict) -> None:
        interval = candle["i"]
        # Check if this is a closing candle
        if candle["x"]:
            try:
                df = self.datasets[interval]
            except KeyError:
                # If there is no data for this candle interval, make a new dataframe for it
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
        # If the candle that was just received isn't a closing candle, update the working_candle
        else:
            candle_series = Series(candle)
            self.working_candle[interval] = candle_series

    #
    # Returns the dataset for a given candle stick interval of a specified size.
    # If there is no size given as a parameter, it will use the default size in __init__
    #
    def get_dataset(self, interval: str, size=None) -> DataFrame:
        size = size if size else self.size
        try:
            # Check if there is current data for this interval
            df = self.datasets[interval][-size:]
            try:
                # Append the working candle to the current data
                wc = self.working_candle[interval]
                return df.append(wc, ignore_index=True)
            except KeyError:
                # There is no working_candle for this interval
                return df[-size:]
        except KeyError:
            try:
                # There is no current data for this interval
                return DataFrame([self.working_candle[interval]])
            except KeyError:
                # There is no current data or working candle for this interval
                return DataFrame()



