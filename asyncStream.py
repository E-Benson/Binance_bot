from binance import ThreadedWebsocketManager
from asyncBuffer import Buffer
from Creds import credentials


api_key = credentials["api_key"]
api_secret = credentials["api_secret"]

INTERVAL_1M = "1m"
INTERVAL_5M = "5m"
INTERVAL_30M = "30m"
INTERVAL_1H = "1h"
INTERVAL_1D = "1d"

data_buffer = Buffer(save_data=True)


def main():
    symbol = "ETHUSDT"
    sock = ThreadedWebsocketManager(api_key, api_secret, tld="us")
    sock.start()

    def on_message(msg):
        data_buffer.recv_candle(msg["k"])
        print(data_buffer)
        #print(data_buffer.get_dataset(msg["k"]["i"]))

    sock.start_kline_socket(callback=on_message, symbol=symbol, interval=INTERVAL_1M)
    sock.start_kline_socket(callback=on_message, symbol=symbol, interval=INTERVAL_5M)

    streams = ["1m candle", "5m candle"]
    sock.start_multiplex_socket(callback=on_message, streams=streams)

    sock.join()


if __name__ == "__main__":
    main()

