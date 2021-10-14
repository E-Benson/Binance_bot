from binance import ThreadedWebsocketManager
from asyncBuffer import Buffer
from Creds import credentials
from StateStrategy import ADXStateTrader, StateTrader, LookingToBuy
from Strategy import Position
import pandas as pd

api_key = credentials["api_key"]
api_secret = credentials["api_secret"]
token = "SHIB"
symbol = f"{token}USDT"
trades_csv_path = f"csvs/{token}_trades.csv"

INTERVAL_1M = "1m"
INTERVAL_5M = "5m"
INTERVAL_30M = "30m"
INTERVAL_1H = "1h"
INTERVAL_1D = "1d"

data_buffer = Buffer(save_data=True)


cur_pos = Position()
window = 5
strategies = {
    INTERVAL_1M: ADXStateTrader(window=window, threshold=20),
    INTERVAL_5M: ADXStateTrader(window=window, threshold=25)
}
env = {
    "data": None,
    "wallet": 500,
    "position": cur_pos,
    "positions": [],
    "trades": pd.DataFrame(columns=["q", "b", "s", "bt", "st", "p"]),
    "strategies": strategies,
    "attempts": 0
}


def clean_candle(candle: dict):
    floats = ["o", "c", "h", "l", "q", "v", "V", "Q"]
    ints = ["t", "T", "f", "L", "n"]
    for k in candle.keys():
        if k in floats:
            candle[k] = float(candle[k])
        elif k in ints:
            candle[k] = int(candle[k])
    return candle


def analyze_trades(df):
    wins = df[df["p"] > 0]
    losses = df[df["p"] < 0]
    return {
        "wins": wins,
        "win_total": wins.sum(),
        "win_size": len(wins),
        "losses": losses,
        "loss_total": losses.sum(),
        "loss_size": len(losses),
        "accuracy": round(len(wins) / len(df) * 100, 3),
        "profit": df["p"].sum(),
    }


def main():
    global env
    global symbol
    sock = ThreadedWebsocketManager(api_key, api_secret, tld="us")
    sock.start()

    trader = StateTrader(env)

    # This is called every time we receive candle data from the Binance server
    def on_message(msg):
        global env
        candle = clean_candle(msg["k"])
        candle_interval = candle["i"]
        # Add the candle we just received to the data buffer
        print(f"Received {candle_interval} candle")
        data_buffer.recv_candle(candle)
        data = data_buffer.get_dataset(candle_interval)
        env["data"] = data

        print(data_buffer)

        # TODO: Pass the data buffer to the strategy to update
        #   Ask the strategy for an action
        #  Also make a new strategy that considers more than one candle interval with states

        if len(data) > window:
            env["strategies"][candle_interval].update_data(data)
            print("\t> Updated env strategy")
            trader.update_data(env)
            env = trader.env
            print(f"\t> {trader.state.name}")
            if isinstance(trader.state, LookingToBuy):
                print("\t> Current wallet: ${:.2f} ({: .2f}) after {} trades".format(env['wallet'],
                                                                                     env['trades']['p'].sum(),
                                                                                     len(env['trades'])))
                if len(env["trades"]):
                    print(env["trades"][["b", "s", "p"]][-10:])
                    env["trades"].to_csv(trades_csv_path, index=False)
                else:
                    print("\t> No trades")
            else:
                print("\t> Current position: amount: {:.6f}, buy price: ${:.7f}".format(env["position"].quantity,
                                                                                        env["position"].buy_price))
                print("\t\t> Current prices: close: {:.6f}, high: {:.6f}, low: {:.6f}")
            #print(env["strategies"][candle_interval].data[["c", "h", "l", "pdma", "ndma", "adx"]][-2:])
        print()

        # TODO: An action should be on of:
        #   Wait to buy, hold position, buy position, sell position
        #  Based on the action, do something in the interface

    sock.start_kline_socket(callback=on_message, symbol=symbol, interval=INTERVAL_1M)
    sock.start_kline_socket(callback=on_message, symbol=symbol, interval=INTERVAL_5M)

    streams = ["1m candle", "5m candle"]
    sock.start_multiplex_socket(callback=on_message, streams=streams)

    sock.join()


if __name__ == "__main__":
    main()

