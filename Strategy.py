from ta.momentum import RSIIndicator, StochRSIIndicator
from ta.trend import EMAIndicator, MassIndex, ADXIndicator, IchimokuIndicator, MACD
from ta.volume import VolumeWeightedAveragePrice
from itertools import permutations


class Position:

    def __init__(self, buy_price=None):
        self.buy_price = buy_price
        self.sell_price = None
        self.quantity = 0
        self.buy_id = None
        self.sell_id = None
        self.buy_time = None
        self.sell_time = None


    def __repr__(self, start="("):
        ret = start
        if self.buy_price:
            ret += "${:.2f}, ".format(float(self.buy_price))
        else:
            ret += "0, "
        if self.sell_price:
            ret += "${:.2f}, ".format(float(self.sell_price))
        else:
            ret += "0, "
        if self.gain() > 0:
            ret += "+"
        else:
            ret += "-"
        return ret + "${:.2f})".format(float(abs(self.gain())))

    def __add__(self, other):
        return self.gain() + other

    def __radd__(self, other):
        if other == 0:
            return self
        return self.__add__(other)

    def gain(self):
        if self.sell_price and self.buy_price:
            return self.sell_price - self.buy_price
        return 0.0

    def value(self, cur_price=None):
        if cur_price:
            return self.quantity * cur_price
        if not self.sell_price:
            return self.quantity * self.buy_price
        return self.quantity * self.sell_price

    def profit(self):
        gain = (self.quantity * self.sell_price) - (self.quantity * self.buy_price)
        fee = 0.001
        return gain - (gain * fee)

    def is_empty(self):
        if not self.buy_price:
            return True
        return False

    def is_closed(self):
        if self.sell_price:
            return True
        return False

    def set_buy(self, price):
        self.buy_price = price

    def set_sell(self, price):
        self.sell_price = price

    def set_quantity(self, quantity):
        self.quantity = quantity

    def set_buyid(self, _id):
        self.buy_id = _id

    def set_sellid(self, _id):
        self.sell_id = _id

    def set_buytime(self, _time):
        self.buy_time = _time

    def set_selltime(self, _time):
        self.sell_time = _time


class Strategy:

    def update_data(self, data):
        self.data = data

    def is_buy(self, index):
        return False

    def is_sell(self, index):
        return False

    def pct_diff(self, x, y):
        diff = x - y
        return diff / ((x + y) / 2) * 100

    def test_strategy(self, start_wallet=100, signals=False):
        positions = []
        position = Position()
        wallet = start_wallet
        wallet_ratio = 1
        if signals:
            buy_signals = list()
        for i in range(len(self.data)):
            if signals:
                if self.is_buy(i):
                    buy_signals.append(True)
                else:
                    buy_signals.append(False)
            if position.is_empty() and self.is_buy(i):
                price = self.data["c"].iloc[i]
                #if (wallet * wallet_ratio)
                quantity = 10 / price if (wallet * wallet_ratio) < 10 else (wallet * wallet_ratio / price)
                position.set_buy(price)
                position.set_buytime(self.data["t"].iloc[i])
                position.set_quantity(quantity)
            elif not position.is_closed() and not position.is_empty() and self.is_sell(i):
                position.set_sell(self.data["c"].iloc[i])
                position.set_selltime(self.data["t"].iloc[i])
                positions.append(position)
                position = Position()
        if signals:
            return buy_signals
        return positions


class RSITrader(Strategy):

    def __init__(self, data, period=6, upper=73, lower=32):
        self.data = None
        self.rsii = None
        self.period = period
        self.upper_threshold = upper
        self.lower_threshold = lower
        self.type = f"RSI ({period}, {upper}, {lower}) Trader"
        self.update_data(data)

    def update_data(self, data):
        self.data = data
        self.update_rsii()
        self.update_rsis()

    def update_rsii(self):
        self.rsii = RSIIndicator(close=self.data["c"],
                                 window=self.period,
                                 fillna=False)

    def update_rsis(self):
        self.rsis = self.rsii.rsi()

    def is_buy(self, index):
        rsi = self.rsis.iloc[index]
        if rsi < self.lower_threshold:
            return True
        return False

    def is_sell(self, index):
        rsi = self.rsis.iloc[index]
        if rsi > self.upper_threshold:
            return True
        return False

    def test_params(self):
        stored_period = self.period
        stored_upper_threshold = self.upper_threshold
        stored_lower_threshold = self.lower_threshold
        best = {
            "period": 0,
            "upper": 0,
            "lower": 0,
            "wallet": 0
        }
        counter = 0

        for period, upper, lower in self.generate_param_perms():
            self.period = period
            self.upper_threshold = upper
            self.lower_threshold = lower
            self.update_rsii()
            self.update_rsis()
            positions = self.test_strategy()
            gain = positions[0].gain() if len(positions) == 1 else sum(positions)
            if gain > best["wallet"]:
                best["period"] = period
                best["upper"] = upper
                best["lower"] = lower
                best["wallet"] = gain
            if counter % 500 == 0:
                print("{}) gain: ${:.2f}\tp: {}, u: {}, l: {}".format(counter,
                                                                      best["wallet"],
                                                                      best["period"],
                                                                      best["upper"],
                                                                      best["lower"]))
            counter += 1
        self.upper_threshold = stored_upper_threshold
        self.lower_threshold = stored_lower_threshold
        self.period = stored_period
        return best

    def generate_param_perms(self):
        for p in range(1,25):
            for u in range(60,100):
                for l in range(1,40):
                    yield p, u, l


class EMATrader(Strategy):

    def __init__(self, data, period=34):
        self.data = None
        self.emai = None
        self.emas = None
        self.period = period
        self.update_data(data)
        self.type = "EMA Trader"

    def update_data(self, data):
        self.data = data
        self.update_emai()
        self.update_emas()

    def update_emai(self):
        self.emai = EMAIndicator(close=self.data["c"],
                                 window=self.period,
                                 fillna=False)

    def update_emas(self):
        self.update_emai()
        self.emas = self.emai.ema_indicator()

    def is_buy(self, index):
        ema = self.emas.iloc[index]
        if self.data["c"].iloc[index] > ema:
            return True
        return False

    def is_sell(self, index):
        ema = self.emas.iloc[index]
        if self.data["c"].iloc[index] < ema:
            return True
        return False

    def test_params(self):
        perms = permutations(list(range(1, 53)), 1)
        stored_period = self.period
        best = {
            "period": 0,
            "wallet": 0
        }
        for p in perms:
            self.period, = p
            self.update_emai()
            self.update_emas()
            positions = self.test_strategy()
            gain = sum(positions)
            if gain > best["wallet"]:
                best["period"] = self.period
                best["wallet"] = gain
        self.period = stored_period
        return best


class MassIndexTrader(Strategy):
    # new 13, 9, 10
    # old 24, 13, 13
    def __init__(self, data, fast_period=13, slow_period=9, threshold=10):
        self.data = None
        self.mii = None
        self.mis = None
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.threshold = threshold
        self.update_data(data)
        self.type = "Mass Index Trader"

    def update_data(self, data, state=None):
        self.data = data
        self.update_mii()
        self.update_mis()

    def update_mii(self):
        self.mii = MassIndex(high=self.data["h"],
                             low=self.data["l"],
                             window_fast=self.fast_period,
                             window_slow=self.slow_period,
                             fillna=False)

    def update_mis(self):
        self.update_mii()
        self.mis = self.mii.mass_index()

    def is_buy(self, index):
        try:
            mi = self.mis.iloc[index]
            pmi = self.mis.iloc[index-1]
            if pmi > self.threshold and mi < pmi and mi < self.threshold:
                return True
        except:
            return False
        return False

    def is_sell(self, index):
        try:
            mi = self.mis.iloc[index]
            pmi = self.mis.iloc[index - 1]
            if pmi > self.threshold and mi < pmi and mi < self.threshold:
                return True
        except:
            return False
        return False

    def test_params(self):
        stored_fast = self.fast_period
        stored_slow = self.slow_period
        stored_threshold = self.threshold
        best = {
            "wallet": 0,
            "fast": 0,
            "slow": 0,
            "threshold": 0
        }
        counter = 0
        for f, s, t in self.generate_test_params():
            self.fast_period = f
            self.slow_period = s
            self.threshold = t
            self.update_mii()
            self.update_mis()
            positions = self.test_strategy()
            gain = positions[0].gain() if len(positions) == 1 else sum(positions)
            if gain > best["wallet"]:
                best["fast"] = f
                best["slow"] = s
                best["threshold"] = t
                best["wallet"] = gain
            if not counter % 500:
                print("{}) gain: ${:.2f}\tf: {}, s: {}, t: {}".format(counter,
                                                                      best["wallet"],
                                                                      best["fast"],
                                                                      best["slow"],
                                                                      best["threshold"]))
            counter += 1
        self.fast_period = stored_fast
        self.slow_period = stored_slow
        self.threshold = stored_threshold

        return best

    def generate_test_params(self):
        for f in range(5,32):
            for s in range(2,14):
                for t in range(1, 28):
                    yield f, s, t


class ADXTrader(Strategy):

    def __init__(self, data, period=20, trend_val=24):
        self.period = period
        self.trend_threshold = trend_val
        self.data = data
        self.update_adxi()
        self.adxs = None
        self.adns = None
        self.adps = None
        self.update_data(data)
        self.type = "ADX Trader"

    def update_data(self, data):
        self.data = data
        self.update_adxi()
        self.update_adxs()

    def update_adxi(self):
        a = self.data["h"]
        b = self.data["l"]
        c = self.data["c"]
        self.adxi = ADXIndicator(high=self.data["h"],
                                 low=self.data["l"],
                                 close=self.data["c"],
                                 window=self.period,
                                 fillna=True)

    def update_adxs(self):
        self.adxs = self.adxi.adx()
        self.adns = self.adxi.adx_neg()
        self.adps = self.adxi.adx_pos()

    def is_buy(self, index):
        trending = self.adxs.iloc[index] > self.trend_threshold
        if trending and self.adns.iloc[index] < self.adps.iloc[index]:
            return True
        return False

    def is_sell(self, index):
        trending = self.adxs.iloc[index] > self.trend_threshold
        if trending and self.adns.iloc[index] > self.adps.iloc[index]:
            return True
        return False

    def test_params(self):
        stored_threshold = self.trend_threshold
        stored_period = self.period
        best = {
            "period": 0,
            "threshold": 0,
            "wallet": 0
        }
        for p, t in self.generate_params():
            self.period = p
            self.trend_threshold = t
            self.update_adxi()
            self.update_adxs()
            positions = self.test_strategy()
            gain = positions[0].gain() if len(positions) == 1 else sum(positions)
            if gain > best["wallet"]:
                best["wallet"] = gain
                best["threshold"] = t
                best["period"] = p
        self.trend_threshold = stored_threshold
        self.period = stored_period
        return best


    def generate_params(self):
        for p in range(2,21):
            for t in range(10,28):
                yield p, t

class IchimokuTrader(Strategy):

    def __init__(self, data, period1=2, period2=6, period3=37): #9, 26, 52
        self.data = None
        self.period1 = period1
        self.period2 = period2
        self.period3 = period3
        self.ichii = None
        self.span_a = None
        self.span_b = None
        self.base_line = None
        self.conv_line = None
        self.update_data(data)
        self.type = "Ichimoku Trader"

    def update_data(self, data):
        self.data = data
        self.update_ichii()
        self.update_ichis()

    def update_ichii(self):
        self.ichii = IchimokuIndicator(high=self.data["h"],
                                       low=self.data["l"],
                                       window1=self.period1,
                                       window2=self.period2,
                                       window3=self.period3,
                                       fillna=True)

    def update_ichis(self):
        self.span_a = self.ichii.ichimoku_a()
        self.span_b = self.ichii.ichimoku_b()
        self.base_line = self.ichii.ichimoku_base_line()
        self.conv_line = self.ichii.ichimoku_conversion_line()

    def is_buy(self, index):
        a = self.span_a.iloc[index]
        b = self.span_b.iloc[index]
        base = self.base_line.iloc[index]
        conversion = self.conv_line[index]
        if a > b:
            if self.data["c"].iloc[index] >= a:
                if conversion > base:
                    return True
        return False

    def is_sell(self, index):
        a = self.span_a.iloc[index]
        b = self.span_b.iloc[index]
        base = self.base_line.iloc[index]
        conversion = self.conv_line[index]

        if b > a or base > conversion or self.data["c"].iloc[index] < a:
            return True
        return False

    def test_params(self):
        stored_p1 = self.period1
        stored_p2 = self.period2
        stored_p3 = self.period3
        best = {
            "p1": 0,
            "p2": 0,
            "p3": 0,
            "wallet": 0
        }
        for p1, p2, p3 in self.generate_params():
            self.period1 = p1
            self.period2 = p2
            self.period1 = p3
            self.update_ichii()
            self.update_ichis()
            positions = self.test_strategy()
            gain = positions[0].gain() if len(positions) == 1 else sum(positions)
            if gain > best["wallet"]:
                best["wallet"] = gain
                best["p1"] = p1
                best["p2"] = p2
                best["p3"] = p3
        self.period1 = stored_p1
        self.period2 = stored_p2
        self.period3 = stored_p3
        return best

    def generate_params(self):
        for p1 in range(2,14):
            for p2 in range(5,35):
                for p3 in range(34,63):
                    yield p1, p2, p3



class StochRSITrader(Strategy):
    # Fitted to 1m 1 day ETH: p: 2, s1: 7, s2: 6, up: 70, low: 15
    def __init__(self, data, period=14, smooth1=3, smooth2=3, upper=80, lower=20):
        self.type = f"Stochastic RSI ({period}, {upper}, {lower}) Trader"
        self.data = None
        self.srsii = None
        self.srsiis = None
        self.srsids = None
        self.srsiks = None
        self.period = period
        self.smooth1 = smooth1
        self.smooth2 = smooth2
        self.upper_threshold = upper
        self.lower_threshold = lower
        self.update_data(data)

    def update_data(self, data):
        self.data = data
        self.update_srsii()
        self.update_srsiis()

    def update_srsii(self):
        self.srsii = StochRSIIndicator(self.data["c"],
                                       window=self.period,
                                       smooth1=self.smooth1,
                                       smooth2=self.smooth2,
                                       fillna=True)

    def update_srsiis(self):
        self.srsiis = self.srsii.stochrsi()
        self.srsids = self.srsii.stochrsi_d()
        self.srsiks = self.srsii.stochrsi_k()

    def is_buy(self, index):
        # k > d = True / Buy
        # k > l_threshold && k-1 < l_threshold
        try:
            indicator = self.srsiis.iloc[index]
            d = self.srsids.iloc[index]
            k = self.srsiks.iloc[index]
            pk = self.srsiks.iloc[index - 1]
            if pk < self.lower_threshold and k < self.lower_threshold:
                return True
            if k > d:
                return True
            #print("i: {: <10.4f} k: {: <10.4f} d: {: <10.4f}".format(indicator, k, d))
            return False
        except:
            return False

    def is_sell(self, index):
        try:
            indicator = self.srsiis.iloc[index]
            d = self.srsids.iloc[index]
            k = self.srsiks.iloc[index]
            pk = self.srsiks.iloc[index - 1]
            if pk > self.upper_threshold and k < self.upper_threshold:
                return True
            if k < d:
                return True
            #print("i: {: <10.4f} k: {: <10.4f} d: {: <10.4f}".format(indicator, k, d))
            return False
        except:
            return False

    def test_params(self):
        stored_p = self.period
        stored_s1 = self.smooth1
        stored_s2 = self.smooth2
        stored_upper = self.upper_threshold
        stored_lower = self.lower_threshold
        best = {
            "wallet": 0,
            "period": 0,
            "s1": 0,
            "s2": 0,
            "upper": 0,
            "lower": 0
        }
        count = 0
        for p, s1, s2, upper, lower in self.generate_params():
            self.period = p
            self.smooth1 = s1
            self.smooth2 = s2
            self.upper_threshold = upper
            self.lower_threshold = lower
            self.update_srsii()
            self.update_srsiis()
            positions = self.test_strategy()
            gain = positions[0].gain if len(positions) == 1 else sum(positions)
            if gain > best["wallet"]:
                best["wallet"] = gain
                best["period"] = p
                best["s1"] = s1
                best["s2"] = s2
                best["upper"] = upper
                best["lower"] = lower
            if not count % 500:
                print("{:<10} p: {:<10} s1: {:<10} s2: {:<10} up: {:<10} low: {:<10} ".format(count, p, s1, s2, upper, lower))
            count += 1
        self.period = stored_p
        self.smooth1 = stored_s1
        self.smooth2 = stored_s2
        self.upper_threshold = stored_upper
        self.lower_threshold = stored_lower
        return best

    def generate_params(self):
        for p in range(2,18):
            for s1 in range(2,9):
                for s2 in range(2,9):
                    for upper in range(70, 95):
                        for lower in range(15, 40):
                            yield p, s1, s2, upper, lower

class MACDTrader(Strategy):

    def __init__(self, data, period_slow=26, period_fast=12, period=9):
        self.type = f"MACD ({period_slow}, {period_fast}, {period}) Trader"
        self.data = None
        self.macdi = None
        self.macdis = None
        self.macdds = None
        self.macdss = None
        self.period_slow = period_slow
        self.period_fast = period_fast
        self.period = period
        self.update_data(data)

    def update_data(self, data):
        self.data = data
        self.update_macdi()
        self.update_macdis()

    def update_macdi(self):
        self.macdi = MACD(close=self.data["c"],
                          window_slow=self.period_slow,
                          window_fast=self.period_fast,
                          window_sign=self.period,
                          fillna=True)

    def update_macdis(self):
        self.macdis = self.macdi.macd()
        self.macdds = self.macdi.macd_diff()
        self.macdss = self.macdi.macd_signal()

    def is_buy(self, index):
        try:
            mi = self.macdis.iloc[index]
            pmi = self.macdis.iloc[index - 1]
            md = self.macdds.iloc[index]
            ms = self.macdss.iloc[index]
            pmis = [self.macdis.iloc[index-n] < 0 for n in range(1, 4)]
            #print("mi: {:<10.3f} md: {: <10.3f} ms: {: <10.3f}".format(mi, md, ms))
            if mi > ms:
                return True
            if 0 < mi and any(pmis):
                return True

        except:
            return False

    def is_sell(self, index):
        try:
            mi = self.macdis.iloc[index]
            pmi = self.macdis.iloc[index - 1]
            md = self.macdds.iloc[index]
            ms = self.macdss.iloc[index]
            pmis = [self.macdis.iloc[index - n] > 0 for n in range(1, 4)]
            #print("mi: {:<10.3f} md: {: <10.3f} ms: {: <10.3f}".format(mi, md, ms))
            if mi < ms:
                return True
            if 0 > mi and any(pmis):
                return True
        except:
            return False
        return False

    def test_params(self):
        best = {
            "period": 0,
            "fast": 0,
            "slow": 0,
            "wallet": 0
        }
        stored_period = self.period
        stored_fast = self.period_fast
        stored_slow = self.period_slow
        count = 0
        for p, f, s in self.generate_params():
            self.period = p
            self.period_fast = f
            self.period_slow = s
            self.update_macdi()
            self.update_macdis()
            positions = self.test_strategy()
            gain = positions[0].gain() if len(positions) == 1 else sum(positions)
            if gain > best["wallet"]:
                best["wallet"] = gain
                best["fast"] = f
                best["period"] = p
                best["slow"] = s
            if not count % 250:
                print("{:<8}) gain: ${:<10.2f} p: {:<10.2f} f: {:<10.2f} s: {:<10.2f}".format(count, gain, p, f, s))
            count += 1
        self.period = stored_period
        self.period_fast = stored_fast
        self.period_slow = stored_slow
        return best


    def generate_params(self):
        for p in range(2,16):
            for f in range(4,24):
                for s in range(9,52):
                    if p < f < s:
                        yield p, f, s


class VWAPTrader(Strategy):

    def __init__(self, data, period=14):
        self.type = f"VWAP ({period}) Trader"
        self.data = None
        self.vwapi = None
        self.vwapis = None
        self.period = period
        self.update_data(data)

    def update_data(self, data):
        self.data = data
        self.update_vwapi()
        self.update_vwapis()

    def update_vwapi(self):
        self.vwapi = VolumeWeightedAveragePrice(high=self.data["h"],
                                                low=self.data["l"],
                                                close=self.data["c"],
                                                volume=self.data["v"],
                                                window=self.period,
                                                fillna=False)

    def update_vwapis(self):
        self.vwapis = self.vwapi.volume_weighted_average_price()

    def is_buy(self, index):
        return self.data["c"].iloc[index] > self.vwapis.iloc[index]

    def is_sell(self, index):
        return self.data["c"].iloc[index] < self.vwapis.iloc[index]

    def test_params(self):
        stored_period = self.period
        best = {
            "period": 0,
            "wallet": 0
        }
        for v in range(2,52):
            self.period = v
            self.update_vwapi()
            self.update_vwapis()
            positions = self.test_strategy()
            gain = positions[0].gain() if len(positions) == 1 else sum(positions)
            if gain > best["wallet"]:
                best["wallet"] = gain
                best["period"] = v
        self.period = stored_period
        return best






