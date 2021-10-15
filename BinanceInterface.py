from binance.client import Client
from binance.enums import *
import pandas as pd
from pandas import DataFrame
import time
from pprint import pprint


client = Client("ljQ8hdKoko74G3jmKcRZvK9OmDC07BNpcbelSIZNGKWx2z4pC80yTWlf9syCsxCt",
                "QVO9tcdKwPOOgh2CMkMRMNADdh5vWl8ctYP1xyKwhvu73eqauWuROgBzYUW9R2y7",
                #testnet=True,
                tld="us")

#depth = client.get_order_book(symbol="ETHUSDT")
candle_labels = ["T", "o", "h", "l", "c",
                     "b", "t", "Q", "n",
                     "v", "V", "x"]
#pprint(depth)

def get_historical_data(symbol: str, candle_size="1m", time_frame="1 day") -> DataFrame:

    data = []
    for candle in client.get_historical_klines_generator(symbol, candle_size, f"{time_frame} ago UTC"):
        cleaned = []
        for v in candle:
            if type(v) is str:
                cleaned.append(float(v))
            else:
                cleaned.append(v)
        data.append(dict(zip(candle_labels, cleaned)))
    return pd.DataFrame(data, columns=candle_labels)


def place_order(symbol: str, quantity: float, price: float, timeInForce="IOC", test=True) -> dict:
    args = {
        "symbol": symbol,
        "side": "BUY",
        "type": "LIMIT",
        "timeInForce": timeInForce,
        "quantity": quantity,
        "price": str(price)
    }
    if test:
        #order = client.create_test_order(**args)
        order = client.create_test_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_IOC,
            quantity=quantity,
            price=price
        )
        return order
    else:
        pass


def place_sell_order(symbol: str, quantity: float, price: float) -> bool:
    if round(quantity, 5) > quantity:
        quantity = (quantity * 100000) // 1 / 100000
    else:
        quantity = round(quantity, 5)
        #print(f"Quantity rounded {quantity}")
    order = client.order_limit_sell(
        symbol=symbol.upper(),
        quantity=quantity,
        timeInForce=TIME_IN_FORCE_IOC,
        price=round(price, 2) # Round token to proper precision
    )
    return order["status"] != "EXPIRED"


def place_buy_order(symbol: str, quantity: float, price: float) -> bool:
    if round(quantity, 5) > quantity:
        quantity = quantity = (quantity * 100000) // 1 / 100000
    else:
        quantity = round(quantity, 5)
        #print(f"Quantity rounded {quantity}")
    order = client.order_limit_buy(
        symbol=symbol.upper(),
        quantity=quantity,
        timeInForce=TIME_IN_FORCE_IOC,
        price=round(price, 2) # Make sure USDT is in proper precision
    )
    #print(order)
    return order["status"] != "EXPIRED"


def get_bidask(symbol: str) -> tuple:
    res = client.get_order_book(symbol=symbol.upper())
    bid = {
        "price": round(float(res["bids"][0][0]), 2),
        "quantity": float(res["bids"][0][1])
    }
    ask = {
        "price": round(float(res["asks"][0][0]), 2),
        "quantity": float(res["asks"][0][1])
    }
    return bid, ask


def get_asset_balance(symbol: str) -> float:
    res = client.get_asset_balance(asset=symbol.upper())
    return float(res["free"])


def get_asset_price(symbol: str) -> float:
    prices = client.get_all_tickers()
    for token in prices:
        if token["symbol"] == symbol.upper():
            return float(token["price"])
    return -1


def get_avg_price(symbol: str) -> float:
    ask, bid = get_bidask(symbol.upper())
    return (ask["price"] + bid["price"]) / 2


def get_open_orders(symbol: str) -> float:
    return client.get_open_orders(symbol=symbol.upper())


def cancel_order(symbol: str, order_id: str) -> dict:
    res = client.cancel_order(
        symbol=symbol.upper(),
        origClientOrderId=order_id
    )
    return res


if __name__ == "__main__":
    tok = "eth"
    symbol = f"{tok}usdt"
    his = get_historical_data("ETHUSDT", candle_size="1d", time_frame="1 month")
    print(his[["o", "h", "l", "c"]])
