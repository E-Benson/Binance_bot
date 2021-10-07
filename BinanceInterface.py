from binance.client import Client
from binance.enums import *
import pandas as pd
import time
from pprint import pprint


client = Client("ljQ8hdKoko74G3jmKcRZvK9OmDC07BNpcbelSIZNGKWx2z4pC80yTWlf9syCsxCt",
                "QVO9tcdKwPOOgh2CMkMRMNADdh5vWl8ctYP1xyKwhvu73eqauWuROgBzYUW9R2y7",
                #testnet=True,
                tld="us")

#depth = client.get_order_book(symbol="ETHUSDT")
candle_labels = ["open_time", "open", "close", "high", "low",
                     "volume", "close_time", "q_volume", "num_trades",
                     "taker_base_vol", "taker_quote_vol", "x"]
#pprint(depth)

def get_historical_data(symbol, candle_size="1m", time_frame="1 day"):

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


def place_order(symbol, quantity, price, timeInForce="IOC", test=True):
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


def place_sell_order(symbol, quantity, price):
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


def place_buy_order(symbol, quantity, price):
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


def get_bidask(symbol):
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


def get_asset_balance(symbol):
    res = client.get_asset_balance(asset=symbol.upper())
    return float(res["free"])


def get_asset_price(symbol):
    prices = client.get_all_tickers()
    for token in prices:
        if token["symbol"] == symbol.upper():
            return float(token["price"])
    return -1


def get_avg_price(symbol):
    ask, bid = get_bidask(symbol.upper())
    return (ask["price"] + bid["price"]) / 2


def get_open_orders(symbol):
    return client.get_open_orders(symbol=symbol.upper())


def check_order_status(symbol, orderId):
    orders = client.get_all_orders(symbol=symbol.upper())
    for order in orderId:
        if order["orderId"] == orderId:
            return order["status"]
    return "Filled?"

def cancel_order(symbol, order_id):
    res = client.cancel_order(
        symbol=symbol.upper(),
        origClientOrderId=order_id
    )
    return res

if __name__ == "__main__":
    #client.cancel_order(symbol="")
    b,a = get_bidask("ETHUSD")

    tok = "eth"
    symbol = f"{tok}usdt"

    #ask_price = a["price"]
    print(f"Highest bid: ${b['price']}")
    print(f"Lowest ask: ${a['price']}")
    price = get_asset_price(symbol)
    print(f"Current price: ${price}")
    print(f"Average price: {(b['price'] + a['price']) / 2}")
    wallet_balance = get_asset_balance(tok)
    print(f"ETH balance: {wallet_balance} (${wallet_balance * price})")
    wallet_balance = get_asset_balance("USDT")
    print(f"USD balance: ${wallet_balance}")
    bid, ask = get_bidask(symbol)
    print(bid, ask)
    buy_quantity = 21 / a["price"]
    print(f"Buy quantity: {buy_quantity}")
    print(f"Buy value: {buy_quantity * a['price']}")
    #place_buy_order("ETHUSD", buy_quantity, a["price"])
    #place_sell_order('ethusdt', 0.02612198, 3029.045)

    #order = place_buy_order('ETHUSDT', buy_quantity, "2500.00")
    #print(order)

    token = "eth"
    symbol = f"{token}usdt"
    ords = get_open_orders(symbol.upper())
    print(ords)

    #for ord in ords:
        #res = cancel_order("ETHUSD", ord["clientOrderId"])
        #print(res)




    #c = client.get_account()
    #pprint(client.get_account())
    #klines = client.get_historical_klines("ETHUSDT", "1m", "5 days ago UTC")
    #klines = client.get_historical_klines("ETHUSDT", "1m", "1 week ago UTC")
    #candles = get_historical_data("ETHUSDT")
    #print(candles)
    #print(klines)
