from pandas import read_csv, DataFrame, Series
from Indicators import ADX
from Strategy import Position
from asyncBuffer import Buffer


class StateStrategy:

    data = None

    def update_data(self, data: DataFrame) -> None:
        pass

    def update_indicator(self) -> None:
        pass

    def is_buy(self, i: int) -> bool:
        pass

    def is_sell(self, i: int) -> bool:
        pass

    def calc_fee(self, value: float) -> float:
        return round(value * 0.001, 2)

    def calc_quantity(self, env: dict, price: float) -> float:
        if env["wallet"] < 10:
            return 0
        return round(env["wallet"] / price, 6)

    def calc_profit(self, position: Position, price: float) -> float:
        fee = self.calc_fee(position.value(cur_price=price))
        cur_value = position.value(cur_price=price) - fee
        return position.value() - cur_value

    def pct_gain(self, profit: float, value: float) -> float:
        return profit / value

    def test_strategy(self, start_wallet=100, ratio=1, signals=False) -> list:
        positions = list()
        cur_pos = Position()
        wallet = start_wallet
        wallet_ratio = ratio
        buy_signals = list()

        def get_quantity(cur_price):
            if wallet * wallet_ratio < 10:
                return 0 if wallet < 10 else 10 / cur_price
            return (wallet * wallet_ratio) / cur_price

        for i, candle in self.data.iterrows():
            if signals:
                if self.is_buy(i):
                    buy_signals.append(True)
                else:
                    buy_signals.append(False)
            else:
                if cur_pos.is_empty() and self.is_buy(i):
                    print("Buying")
                    cur_pos.set_buy(self.data.loc[i]["c"])
                    cur_pos.set_buytime(self.data.loc[i]["t"])
                    cur_pos.quantity = get_quantity(self.data.loc[i]["c"])
                elif not cur_pos.is_closed() and not cur_pos.is_empty() and self.is_sell(i):
                    print("selling")
                    cur_pos.set_sell(self.data.loc[i]["c"])
                    cur_pos.set_selltime(self.data.loc[i]["t"])
                    positions.append(cur_pos)
                    cur_pos = Position()
        if signals:
            return buy_signals
        return positions


class ADXStateTrader(StateStrategy):

    window = 0
    stoploss = 0
    threshold = 0
    ind = None
    data = None
    adx = None
    adp = None
    adn = None

    def __init__(self, window=14, threshold=50) -> None:
        self.window = window
        self.threshold = threshold

    def update_data(self, data: DataFrame) -> None:
        self.data = data.copy()

        self.update_indicator()

    def update_indicator(self) -> None:
        self.ind = ADX(self.data, period=self.window)
        if len(self.data) > self.window * 2:
            self.adx = self.ind.adx()
            self.adp = self.ind.adx_pos()
            self.adn = self.ind.adx_neg()

    def update_stoploss(self, stoploss: float, trending: int) -> None:
        self.stoploss = stoploss

    def is_buy(self, i: int) -> bool:
        if self.adx is None:
            return False
        if self.adx.iloc[i] > self.threshold:
            if self.adp.iloc[i] > self.adn.iloc[i]:
                self.update_stoploss(self.data.iloc[i]["l"], 1)
                return True
        return False

    def is_sell(self, i: int) -> bool:
        if self.adx is None:
            return False
        if self.data.iloc[i]["c"] < self.stoploss:
            return True
        self.update_stoploss(self.data.iloc[i]["l"], 1)
        return False


class State:

    def __init__(self, env: dict):
        self.env = env

    def process(self, env: dict):
        pass

    def action(self):
        return self.env

    def calc_quantity(self, wallet: float, price: float) -> float:
        if wallet < 10:
            return 0.0
        return round(wallet / price, 6)


class LookingToBuy(State):
    name = "LookingToBuy"

    def process(self, env: dict):
        self.env = env
        if all([s.is_buy(-1) for s in self.env["strategies"].values()]):
            return TryingToBuy(self.env)
        return self


class TryingToBuy(State):
    name = "\t> TryingToBuy..."

    def process(self, env: dict):
        self.env = env
        if not self.env["position"].is_empty():
            return HoldingPosition(self.env)
        if self.env["attempts"] > 5:
            self.env["attempts"] = 0
            return LookingToBuy(self.env)
        return self

    def action(self):
        self.env["position"].set_buy(self.env["data"].iloc[-1]["c"])
        self.env["position"].set_buytime(self.env["data"].iloc[-1]["t"])
        quantity = self.calc_quantity(self.env["wallet"], self.env["data"].iloc[-1]["c"])
        self.env["position"].set_quantity(quantity)
        return self.env


class HoldingPosition(State):
    name = "\t> HoldingPosition"

    def process(self, env: dict):
        self.env = env
        if self.env["attempts"] > 2:
            self.env["attempts"] = 0
            return LookingToSell(self.env)
        return self

    def action(self):
        tmp_env = self.env.copy()
        tmp_env["attempts"] += 1
        return tmp_env


class LookingToSell(State):
    name = "\t> LookingToSell"

    def process(self, env: dict):
        self.env = env
        if any([s.is_sell(-1) for s in self.env["strategies"].values()]):
            return TryingToSell(self.env)
        return self


class TryingToSell(State):
    name = "\t>> TryingToSell..."

    def process(self, env: dict):
        self.env = env
        if self.env["position"].is_closed():
            self.env["attempts"] = 0
            self.env["position"] = Position()
            return LookingToBuy(self.env)
        if self.env["attempts"] > 5:
            self.env["attempts"] = 0
            return LookingToSell(self.env)
        return self

    def action(self):
        self.env["position"].set_sell(self.env["data"].iloc[-1]["c"])
        self.env["position"].set_selltime(self.env["data"].iloc[-1]["t"])
        trade_series = Series(self.env["position"].to_array(), index=["q", "b", "s", "bt", "st", "p"])
        self.env["trades"] = self.env["trades"].append(trade_series, ignore_index=True)
        self.env["wallet"] += self.env["position"].profit()
        return self.env


class StateTrader:

    def __init__(self, env: dict):
        self.state = LookingToBuy(env)
        self.env = env

    def update_data(self, env: dict):
        self.env["data"] = env["data"]
        self.state = self.state.process(self.env)
        self.env = self.state.action()
        return self.env


if __name__ == "__main__":
    import cProfile
    import pstats
    strats = {
        "1m": ADXStateTrader()
    }
    df = read_csv("csvs/ETHUSDT_3day_history.csv").drop("Unnamed: 0", axis=1)
    df["i"] = Series(["1m"] * len(df))
    db = Buffer(save_data=False)
    env = {
        "data": None,
        "position": Position(),
        "positions": list(),
        "strategies": strats,
        "attempts": 0
    }
    sm = StateTrader(env)
    print("Starting profiling")
    pr = cProfile.Profile()
    pr.enable()
    for i, series in df[:500].iterrows():
        db.recv_candle(series)
        data = db.get_dataset("1m")

        env["data"] = db.get_dataset("1m")
        if i > 5:
            env["strategies"]["1m"].update_data(db.get_dataset("1m"))
            sm.update_data(env)
    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    #stats.dump_stats(filename="profile_out3.prof")



