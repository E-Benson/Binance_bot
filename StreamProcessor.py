import websocket, json
from pprint import pprint
import pandas as pd
from Strategy import Position, MACDTrader
import BinanceInterface as bi
from binance.exceptions import BinanceAPIException

token = "eth"
symbol = f"{token}usdt"
interval = "1m"
uri = f"wss://stream.binance.com:9443/ws/{symbol}@kline_{interval}"
data_csv_path = "csvs/bot_df.csv"
trade_csv_path = "csvs/bot_tr.csv"

wallet_ratio = 1.0
state = {
    "position": Position(),
    "positions": [],
    "wallet": 0,
    "failed_orders": 0,
    "start_wallet": bi.get_asset_balance("USDT")
}
cols = ["open", "close", "high", "low", "volume", "time"]
trade_cols = ["buy_price", "buy_time", "sell_price", "sell_time"]
waiting = 9
positions = pd.DataFrame(columns=trade_cols)

def get_buy_quantity(state, price):
    if state["wallet"] < 10:
        return 0
    quantity = (state["wallet"] * wallet_ratio) / price
    if quantity * price < 10:
        return 10 / price
    if quantity < 0.0000001:
        return 0
    return quantity


def process_candle(candle):
    candle_data = dict()
    candle_data["open"] = float(candle["o"])
    candle_data["close"] = float(candle["c"])
    candle_data["high"] = float(candle["h"])
    candle_data["low"] = float(candle["l"])
    candle_data["volume"] = float(candle["q"])
    candle_data["time"] = candle["T"]
    return pd.Series(candle_data)


def on_open(socket):
    pprint("Opened...")


def on_close(socket):
    pprint("Closed...")


def on_message(socket, message):
    data = json.loads(message)
    global df
    global strategy
    global state
    global waiting
    global positions
    candle_data = process_candle(data['k'])
    # Is this the end of the candle stick?
    if data["k"]["x"]:
        df = df.append(candle_data, ignore_index=True)
        strategy.update_data(df)
        print(f"({waiting})", end="")
        waiting = 0 if waiting - 1 < 0 else waiting - 1
    # Candle stick is still open
    else:
        strategy.update_data(df.append(candle_data, ignore_index=True))
    # Ensure the dataframe is reasonably short
    if df.size > 101:
        df = df[-100:]
    # We are not currently holding a token
    if waiting:
        print("=", end="")
    elif state["position"].is_empty():
        # Strategy thinks we should buy
        if strategy.is_buy(-1) and strategy.is_buy(-2):
            # Make buy order
            try:
                state["wallet"] = bi.get_asset_balance("USDT")
            except BinanceAPIException as e:
                print(f"\t|- Error getting balance - {e}")
                return
            _, ask = bi.get_bidask(symbol)
            price = ask["price"]
            quantity = get_buy_quantity(state, price)
            _time = candle_data["time"]
            # print(price, quantity)
            if quantity:
                #print()
                print("\n\t|- Placing buy order for {:.5f} {} at ${:.2f}".format(quantity, token.upper(), price))
                try:
                    if bi.place_buy_order(symbol, quantity, price):
                        print("\t|---- Buy order placed successfully")
                        state["position"].set_buy(price)
                        state["position"].set_quantity(quantity)
                        state["position"].set_buytime(_time)
                        print("\t|---- Bought in at ${:.2f} x{:.5f}".format(price, quantity))
                        waiting = 2
                    else:
                        print(f"\t|---> Order was not filled {symbol, quantity, price}")
                except BinanceAPIException as e:
                    print(f"\tError placing buy order {symbol, quantity, price}")
                    print(f"\t> wallet: {state['wallet']}")
                    print(f"\t> {e}")
        # Not holding a token, but shouldn't buy either
        else:
            print(f".", end="")
    # We are currently holding some position
    else:
        if strategy.is_sell(-1) and strategy.is_sell(-2):
            # Make sell order
            if state["failed_orders"] < 2:
                price = bi.get_avg_price(symbol)
                cur_value = price * state["position"].quantity
                buy_value = state["position"].buy_price * state["position"].quantity
                # if we are profiting try to ensure we make money after fees
                if cur_value >= buy_value:
                    target_price = ((buy_value + 0.02) * 0.999) / state["position"].quantity
                    price = price if price > target_price else target_price
            else:
                bid, _ = bi.get_bidask(symbol)
                price = bid["price"]
            quantity = bi.get_asset_balance(token)
            _time = candle_data["time"]
            if quantity:
                print("\n\t|- Placing sell order for ${:.2f} at {}".format(price, quantity))
                try:
                    if bi.place_sell_order(symbol, quantity, price):
                        print("\t|---- Sell order placed successfully")
                        state["position"].set_sell(price)
                        state["position"].set_selltime(_time)
                        trade_data = [state["position"].buy_price, state["position"].buy_time, price, _time ]
                        #print("Appending to positions")
                        trade_series = pd.Series(dict(zip(trade_cols, trade_data)))
                        #print(trade_series)
                        positions = positions.append(trade_series, ignore_index=True)
                        #print("Making new position")
                        #state["positions"].append(state["position"])
                        state["position"] = Position()
                        try:
                            state["wallet"] = bi.get_asset_balance("USDT")
                            print("\t|- ${:.2f}".format(state["wallet"]))
                        except BinanceAPIException as e:
                            print(f"\t Error getting balance for USDT - {e}")
                        #print("\t|- Balance: ${.2f} after {} trades".format(state["wallet"], positions.size))
                        state["failed_orders"] = 0
                        waiting = 4
                        print(f"|- Waiting set to 4")
                    else:
                        print(
                            f"\t|---- Sell order was not filled {symbol, quantity, price} ({state['failed_orders']}/3)")
                        state["failed_orders"] += 1
                except BinanceAPIException as e:
                    print(f"\tError placing sell order {symbol, quantity, price}")
                    print(f"\t> wallet: {state['wallet']}")
                    print(f"\t> {e}")
        # Currently holding a position, but not selling it
        else:
            # Received a closing candle as a message
            if data["k"]["x"]:
                print("\n\t|", end="")
    # Save the current working dataframe to a csv
    df.to_csv(data_csv_path)
    positions.to_csv(trade_csv_path)




df = pd.DataFrame(columns=cols)
strategy = MACDTrader(df, period_slow=9, period_fast=6, period=2)

ws = websocket.WebSocketApp(uri, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
