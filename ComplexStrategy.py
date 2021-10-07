from Logic import Val, Expr, LT, GT, OR, AND, MINUS, PLUS
from Strategy import ADXTrader, IchimokuTrader, EMATrader, RSITrader, MassIndexTrader, Position, Strategy
from Strategy import StochRSITrader, VWAPTrader, MACDTrader


class ComplexStrategy(Strategy):

    def __init__(self, data):
        self.data = data

    def update_data(self, data, state=None):
        self.data = data

    def test_strategy(self, start_wallet=100, ratio=1.0):
        state = {
            "wallet": start_wallet,
            "position": Position(),
            "positions": []
        }
        wallet_ratio = ratio
        for i in range(len(self.data)):
            if state["position"].is_empty() and self.is_buy(i=i):
                price = self.data["close"].iloc[i]
                quantity = 10 / price if (state["wallet"] * wallet_ratio) < 10 else (state["wallet"] * wallet_ratio / price)
                state["position"].set_buy(price)
                state["position"].set_quantity(quantity)
            elif not state["position"].is_empty() and not state["position"].is_closed():
                if self.is_sell(state=state, i=i):
                    state["position"].set_sell(self.data["close"].iloc[i])
                    state["positions"].append(state["position"])
                    state["position"] = Position()
        return state["positions"]

    def build_buy_condition(self, state=None, i=-1):
        return AND(False, False)

    def build_sell_condition(self, state=None, i=-1):
        return AND(False, False)

    def is_buy(self, state=None, i=-1):
        c = self.build_buy_condition(state=state, i=i)
        return c.eval()

    def is_sell(self, state=None, i=-1):
        c = self.build_sell_condition(state=state, i=i)
        return c.eval()


class CS1(ComplexStrategy):

    def __init__(self, data):
        super().__init__(data)
        self.type = "CS1"
        self.EMAT = EMATrader(data)
        self.RSIT = RSITrader(data)
        self.update_data(data)
        self.buy_condition = None
        self.sell_condition = None
        self.build_conditions()

    def build_conditions(self):
        self.build_buy_condition()
        self.build_sell_condition()

    def build_buy_condition(self, state=None, i=1):
        emac = GT(self.EMAT.data["close"].iloc[i], self.EMAT.emas.iloc[i])
        rsic = LT(self.RSIT.rsis.iloc[i], self.RSIT.lower_threshold)
        cond = AND(emac, rsic)
        return cond

    def build_sell_condition(self, state=None, i=-1):
        emac = LT(self.EMAT.data["close"].iloc[i], self.EMAT.emas.iloc[i])
        rsic = GT(self.RSIT.rsis.iloc[i], self.RSIT.upper_threshold)
        cond = OR(emac, rsic)
        return cond

    def update_data(self, data, state=None):
        self.data = data
        self.EMAT.update_data(data)
        self.RSIT.update_data(data)
        self.build_conditions()

    def is_buy(self, state=None, i=-1):
        c = self.build_buy_condition(i=i)
        return c.eval()

    def is_sell(self, state=None, i=-1):
        c = self.build_sell_condition(i=i)
        return c.eval()


class CS2(ComplexStrategy):
    def __init__(self, data):
        super().__init__(data)
        self.type = "CS2"
        self.EMAT = EMATrader(data)
        self.update_data(data)
        self.buy_condition = None
        self.sell_condition = None
        self.build_conditions()

    def build_conditions(self):
        self.build_buy_condition()
        self.build_sell_condition()

    def build_buy_condition(self, state=None, i=1):
        emac = GT(self.EMAT.data["close"].iloc[i], self.EMAT.emas.iloc[i])
        return emac

    def build_sell_condition(self, state=None, i=-1):
        emac = LT(self.EMAT.data["close"].iloc[i], self.EMAT.emas.iloc[i])
        return emac

    def update_data(self, data, state=None):
        self.data = data
        self.EMAT.update_data(data)
        self.build_conditions()

    def is_buy(self, state=None, i=-1):
        c = self.build_buy_condition(i=i)
        return c.eval()

    def is_sell(self, state=None, i=-1):
        c = self.build_sell_condition(i=i)
        return c.eval()


class CS3(ComplexStrategy):
    def __init__(self, data):
        super().__init__(data)
        self.type = "CS3"
        self.EMAT = EMATrader(data)
        self.MSIT = MassIndexTrader(data)
        self.update_data(data)
        self.buy_condition = None
        self.sell_condition = None
        self.build_conditions()

    def build_conditions(self):
        self.build_buy_condition()
        self.build_sell_condition()

    def build_buy_condition(self, state=None, i=1):
        emac = GT(self.EMAT.data["close"].iloc[i], self.EMAT.emas.iloc[i])
        msic = GT(self.MSIT.mis.iloc[i], self.MSIT.threshold)
        cond = AND(emac, msic)
        return cond

    def build_sell_condition(self, state=None, i=-1):
        emac = LT(self.EMAT.data["close"].iloc[i], self.EMAT.emas.iloc[i])
        msic = GT(self.MSIT.mis.iloc[i], self.MSIT.threshold)
        cond = AND(emac, msic)
        return cond

    def update_data(self, data, state=None):
        self.data = data
        self.EMAT.update_data(data)
        self.MSIT.update_data(data)
        self.build_conditions()

    def is_buy(self, state=None, i=-1):
        c = self.build_buy_condition(i=i)
        return c.eval()

    def is_sell(self, state=None, i=-1):
        c = self.build_sell_condition(i=i)
        return c.eval()


class CS4(ComplexStrategy):
    def __init__(self, data, stop_loss=-0.001, stop_gain=-0.1):
        super().__init__(data)
        self.type = "CS3"
        self.stop_loss = stop_loss
        self.stop_gain = stop_gain
        self.EMAT = EMATrader(data)
        self.MSIT = MassIndexTrader(data)
        self.update_data(data)
        self.buy_condition = None
        self.sell_condition = None
        #self.build_conditions()

    def build_conditions(self, state):
        self.build_buy_condition()
        self.build_sell_condition(state)

    def build_buy_condition(self, state=None, i=1):
        emac = GT(self.EMAT.data["close"].iloc[i], self.EMAT.emas.iloc[i])
        msic = GT(self.MSIT.mis.iloc[i], self.MSIT.threshold)
        cond = AND(emac, msic)
        return cond

    def build_sell_condition(self, state=None, i=-1):
        cur_price = self.EMAT.data["close"].iloc[i]
        cur_value = state["position"].value(cur_price)
        diff = self.pct_diff(state["position"].value(), cur_value)
        emac = LT(self.EMAT.data["close"].iloc[i], self.EMAT.emas.iloc[i])
        msic = GT(self.MSIT.mis.iloc[i], self.MSIT.threshold)
        stop_loss = GT(diff, self.stop_loss)
        signal = AND(emac, msic)

        cond = OR(signal, stop_loss)
        return cond

    def update_data(self, data, state=None):
        self.data = data
        self.EMAT.update_data(data)
        self.MSIT.update_data(data)

    def is_buy(self, state=None, i=-1):
        c = self.build_buy_condition(state=state, i=i)
        return c.eval()

    def is_sell(self, state=None, i=-1):
        c = self.build_sell_condition(state=state, i=i)
        return c.eval()


class CS5(ComplexStrategy):
    def __init__(self, data, stop_loss=0.07, stop_gain=-0.1):
        super().__init__(data)
        self.type = "Complex Strategy 5"
        self.stop_loss = stop_loss
        self.stop_gain = stop_gain
        self.MSIT = MassIndexTrader(data)
        self.RSIT = RSITrader(data)
        self.update_data(data)
        self.buy_condition = None
        self.sell_condition = None

    def update_data(self, data, state=None):
        self.data = data
        self.MSIT.update_data(data)
        self.RSIT.update_data(data)

    def build_buy_condition(self, state=None, i=-1):
        mi = self.MSIT.mis.iloc[i]
        rsi = self.RSIT.rsis.iloc[i]
        try:
            pmi = self.MSIT.mis.iloc[i-1]
            mic = GT(pmi, self.MSIT.threshold)
            mic2 = LT(mi, pmi)
            mic = AND(mic, mic2)
            micc = AND(mic, LT(mi, self.MSIT.threshold))
            rsic = LT(rsi, self.RSIT.lower_threshold)
            return micc
        except:
            return AND(False, False)

    def build_sell_condition(self, state=None, i=-1):
        mi = self.MSIT.mis.iloc[i]
        rsi = self.RSIT.rsis.iloc[i]
        try:
            buy_value = state["position"].value()
            cur_value = state["position"].quantity * self.data["close"].iloc[i]
            pct_gain = self.pct_diff(buy_value, cur_value)
            stop_loss = GT(pct_gain, self.stop_loss)
            stop_gain = LT(pct_gain, self.stop_gain)
            losses = OR(stop_loss, stop_gain)
            return OR(self.MSIT.is_sell(i), losses)
        except:
            return AND(False, False)

class CS6(ComplexStrategy):
    def __init__(self, data, stop_loss=0.7, stop_gain=-0.1):
        super().__init__(data)
        self.type = "ADX / Ichimoku Strategy"
        self.stop_loss = stop_loss
        self.stop_gain = stop_gain
        self.ADXT = ADXTrader(data)
        self.ICHIT = IchimokuTrader(data)
        self.update_data(data)
        self.buy_condition = None
        self.sell_condition = None

    def update_data(self, data, state=None):
        self.data = data
        self.ADXT.update_data(data)
        self.ICHIT.update_data(data)

    def build_buy_condition(self, state=None, i=-1):
        return AND(self.ADXT.is_buy(i), self.ICHIT.is_buy(i))

    def build_sell_condition(self, state=None, i=-1):
        return OR(self.ADXT.is_sell(i), self.ICHIT.is_sell(i))


class CS7(ComplexStrategy):

    def __init__(self, data, period_short=9, period_long=34, stop_gain=0.1, stop_loss=0.05):
        super().__init__(data)
        self.type = f"EMA({period_short}) / EMA({period_long}) / Ichimoku Cloud / Gain/Loss {stop_gain, stop_loss}"
        self.period_short = period_short
        self.period_long = period_long
        self.EMAT_s = EMATrader(data, period=period_short)
        self.EMAT_l = EMATrader(data, period_long)
        self.ICHIT = IchimokuTrader(data, period1=2, period2=8, period3=54)
        self.ming = MinGainTrader(data)
        self.minl = MinLossTrader(data)
        self.update_data(data)

    def update_data(self, data, state=None):
        self.data = data
        self.EMAT_s = EMATrader(data, period=self.period_short)
        self.EMAT_l = EMATrader(data, period=self.period_long)
        self.ICHIT = IchimokuTrader(data, period1=2, period2=8, period3=54)
        self.ming.update_data(data)
        self.minl.update_data(data)

    def build_buy_condition(self, state=None, i=-1):
        ema_s = self.EMAT_s.emas.iloc[i]
        ema_l = self.EMAT_l.emas.iloc[i]
        cur_price = self.data["close"].iloc[i]
        ema_cond = OR(GT(cur_price, ema_s), GT(ema_s, ema_l))
        return AND(ema_cond, self.ICHIT.is_buy(i))

    def build_sell_condition(self, state=None, i=-1):
        ema_s = self.EMAT_s.emas.iloc[i]
        ema_l = self.EMAT_l.emas.iloc[i]
        cur_price = self.data["close"].iloc[i]
        scrape = OR(self.ming.build_sell_condition(state=state, i=i), self.minl.build_sell_condition(state=state, i=i))
        ema_cond = OR(LT(cur_price, ema_s), LT(ema_s, ema_l))
        ichic = AND(ema_cond, self.ICHIT.is_sell(i))
        return AND(ichic, scrape)

    def test_params(self):
        best = {
            "period_s": 0,
            "period_l": 0,
            "wallet": 0
        }
        counter = 0

        for short, long in self.generate_parmas():
            self.EMAT_s = EMATrader(self.data, period=short)
            self.EMAT_l = EMATrader(self.data, period=long)
            positions = self.test_strategy()
            gain = positions[0].gain() if len(positions) == 1 else sum(positions)
            if gain > best["wallet"]:
                best["period_s"] = short
                best["period_l"] = long
                best["wallet"] = gain
            if not counter % 500:
                print("{}) gain: ${:.2f}\tshort: {} long: {}".format(counter, gain, short, long))
            counter += 1
        self.EMAT_s = self.period_short
        self.EMAT_l = self.period_long
        return best



    def generate_parmas(self):
        for s in range(2,14):
            for l in range(5,52):
                yield s, l


# StochRSI, MACD
class DeanStrat(ComplexStrategy):

    def __init__(self, data, macd_p=12, macd_s=3, macd_f=5, rsi_p=60, rsi_upper=80, rsi_lower=20, vwap_p=14):
        super().__init__(data)
        self.data = None
        self.srsi = None
        self.macdi = None
        self.vwapi = None
        self.ming = MinGainTrader(data)
        self.minl = MinLossTrader(data)
        self.type = "Na'Ed's Trader"
        self.macd_p = macd_p
        self.macd_s = macd_s
        self.macd_f = macd_f
        self.vwap_p = vwap_p
        self.rsi_p = rsi_p
        self.rsi_lower = rsi_lower
        self.rsi_upper = rsi_upper
        self.update_data(data)

    def update_data(self, data, state=None):
        self.data = data
        self.srsi = StochRSITrader(data, period=self.rsi_p, upper=self.rsi_upper, lower=self.rsi_lower)
        self.macdi = MACDTrader(data, period=self.macd_p, period_slow=self.macd_s, period_fast=self.macd_f)
        self.vwapi = VWAPTrader(data, period=self.vwap_p)
        self.ming.update_data(data)
        self.minl.update_data(data)

    def build_buy_condition(self, state=None, i=-1):
        return AND(self.vwapi.is_buy(i), AND(self.srsi.is_buy(i), self.macdi.is_buy(i)))

    def build_sell_condition(self, state=None, i=-1):
        dean = OR(self.vwapi.is_sell(i), OR(self.srsi.is_sell(i), self.macdi.is_sell(i)))
        stop = OR(self.ming.build_sell_condition(state=state, i=i), self.minl.build_sell_condition(state=state, i=i))
        return AND(dean, stop)

    def test_params(self):
        stored_v = self.vwap_p
        stored_mp = self.macd_p
        stored_mf = self.macd_f
        stored_ms = self.macd_s
        stored_r = self.rsi_p
        best = {
            "wallet": 0,
            "v": 0,
            "mp": 0,
            "mf": 0,
            "ms": 0,
            "r": 0
        }
        count = 0
        for v, mp, mf, ms, r in self.generate_params():
            self.vwap_p = v
            self.vwapi.update_vwapi()
            self.vwapi.update_vwapis()
            self.macd_p = mp
            self.macd_f = mf
            self.macd_s = ms
            self.macdi.update_macdi()
            self.macdi.update_macdis()
            self.rsi_p = r
            self.srsi.update_srsii()
            self.srsi.update_srsiis()

            positions = self.test_strategy()
            gain = positions[0].gain() if len(positions) == 1 else sum(positions)
            if gain > best["wallet"]:
                best["wallet"] = gain
                best["v"] = v
                best["mp"] = mp
                best["mf"] = mf
                best["ms"] = ms
                best["r"] = r
            if not count % 1000:
                pass
                print("{:<10} ${:<10.2f} v: {:<10} mp: {:<10} mf: {:<10} ms: {:<10} r: {:<10}".format(count, best["wallet"], best["v"], best["mp"], best["mf"], best["ms"], best["r"]))
                print("{:<10} ${:<10.2f} v: {:<10} mp: {:<10} mf: {:<10} ms: {:<10} r: {:<10}".format("", gain, v, mp, mf, ms, r))
            count += 1
        return best

    def generate_params(self):
        for v in range(7,34):
            for mp in range(3,21):
                for mf in range(3,18):
                    for ms in range(4,32):
                        for r in range(2,18):
                            if ms > mf > mp:
                                yield v, mp, mf, ms, r


class MinGainTrader(ComplexStrategy):

    def __init__(self, data, min_gain=0.1, fee=0.001):
        super().__init__(data)
        self.type = f"Min. Gain ({min_gain})"
        self.data = None
        self.fee = fee
        self.min_gain = min_gain
        self.update_data(data)

    def update_data(self, data, state=None):
        self.data = data

    def update_gains(self):
        dif = lambda w: w[1] - w[0]
        self.data["gain"] = self.data["close"].rolling(2).apply(dif)

    def build_buy_condition(self, state=None, i=-1):
        return AND(False, False)

    def build_sell_condition(self, state=None, i=-1):
        buy_value = state["position"].value()
        cur_value = (state["position"].quantity * self.data["close"].iloc[i]) * (1 - self.fee)
        dif = self.pct_diff(cur_value, buy_value)
        return GT(dif, self.min_gain)


class MinLossTrader(ComplexStrategy):

    def __init__(self, data, stop_loss=0.05, fee=0.001):
        super().__init__(data)
        self.data = None
        self.fee = fee
        self.type = f"Min. Loss ({stop_loss})"
        self.stop_loss = stop_loss
        self.update_data(data)

    def update_data(self, data, state=None):
        self.data = data

    def build_buy_condition(self, state=None, i=-1):
        return AND(False, False)

    def build_sell_condition(self, state=None, i=-1):
        buy_value = state["position"].value()
        cur_value = (state["position"].quantity * self.data["close"].iloc[i]) * (1 - self.fee)
        dif = self.pct_diff(cur_value, buy_value)
        return LT(dif, self.stop_loss)


class MACDStopTrader(ComplexStrategy):

    def __init__(self,data, stop_loss=0.05, stop_gain=0.1):
        super().__init__(data)
        self.type = f"MACD / Gain/Loss {stop_gain, stop_loss}"
        self.data = None
        self.macdi = None
        self.ming = MinGainTrader(data, min_gain=stop_gain)
        self.minl = MinLossTrader(data, stop_loss=stop_loss)
        self.update_data(data)

    def update_data(self, data, state=None):
        self.data = data
        self.macdi = MACDTrader(data, period_slow=9, period_fast=6, period=2)
        self.ming.update_data(data)
        self.minl.update_data(data)

    def build_buy_condition(self, state=None, i=-1):
        return AND(self.macdi.is_buy(i), True)

    def build_sell_condition(self, state=None, i=-1):
        loss = self.minl.build_sell_condition(state=state, i=i)
        gain = self.ming.build_sell_condition(state=state, i=i)
        stop = OR(gain, loss)
        return AND(self.macdi.is_sell(i), stop)