import os
from dotenv import load_dotenv

load_dotenv()

import alpaca_trade_api as alpaca
import requests
import asyncio


# Alpaca set up
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
HEADERS = {
    "APCA-API-KEY-ID": os.getenv("alpaca_key"),
    "APCA-API-SECRET-KEY": os.getenv("alpaca_secret"),
}
DATA_URL = "https://data.alpaca.markets"


class TriangleArbitrage:
    def __init__(
        self,
        pairs: list = ["ETH/USD", "BTC/USD", "ETH/BTC"],
        sleeptime: int = 3,
        sleepunit: str = "M",
        min_arb_percent: float = 0.3,
    ) -> None:

        # Initialize dictionary
        self.pairs = {symbol: 0 for symbol in pairs}
        self.pairA = pairs[0]
        self.pairB = pairs[1]
        self.pairC = pairs[2]
        self.sleeptime = sleeptime
        self.sleepunit = sleepunit
        self.min_arb_percent = min_arb_percent
        self.rest_api = alpaca.REST(
            os.getenv("alpaca_key"), os.getenv("alpaca_secret"), ALPACA_BASE_URL
        )
        self.spreads = []
        self.markets = ["USD", "EUR"]

    async def get_quote(self, symbol: str):
        """
        Get quote data from Alpaca API
        """
        # symbol = symbol.replace("/", "")
        url = "{0}/v1beta2/crypto/latest/trades?symbols={1}".format(DATA_URL, symbol)
        print(f"URL: {url}")
        try:
            # # make the request
            # quote = requests.get(
            #     "{0}/v1beta3/crypto/latest/trades?symbols={1}".format(DATA_URL, symbol),
            #     headers=HEADERS,
            # )
            # print(f"Quote: {quote}")
            # self.pairs[symbol] = quote.json()["trades"][symbol]["p"]
            # # Status code 200 means the request was successful
            # if quote.status_code != 200:
            #     print("Undesirable response from Alpaca! {}".format(quote.json()))
            #     return False

            quote = self.rest_api.get_latest_crypto_trades(symbols=[symbol])
            quote = quote[symbol].p

            print(f"Quote: {quote}")
            self.pairs[symbol] = quote

        except Exception as e:
            print("There was an issue getting trade quote from Alpaca: {0}".format(e))
            return False

    async def check_arb(self):
        """
        Check to see if an arbitrage condition exists
        """
        pairA = self.pairs[self.pairA]  # ETH/USD
        pairB = self.pairs[self.pairB]  # BTC/USD
        pairC = self.pairs[self.pairC]  # ETH/BTC
        DIV = pairA / pairB
        spread = abs(DIV - pairC)
        BUY_A = 1000 / pairA  # BUY_ETH
        BUY_B = 1000 / pairB  # BUY_BTC
        BUY_C = BUY_B / pairC
        SELL_C = BUY_A / pairC

        if self.pairA.split("/")[1] not in self.markets:
            symbolA = self.pairA.replace("/", "")
        else:
            symbolA = self.pairA
        if self.pairB.split("/")[1] not in self.markets:
            symbolB = self.pairB.replace("/", "")
        else:
            symbolB = self.pairB
        if self.pairC.split("/")[1] not in self.markets:
            symbolC = self.pairC.replace("/", "")
            symbolC = self.pairC
        else:
            symbolC = self.pairC

        # when BTC/USD is cheaper
        if DIV > pairC * (1 + self.min_arb_percent / 100):
            order1 = self.post_Alpaca_order(symbolB, BUY_B, "buy")
            if order1.status_code == 200:
                order2 = self.post_Alpaca_order(symbolC, BUY_C, "buy")
                if order2.status_code == 200:
                    order3 = self.post_Alpaca_order(symbolC, BUY_C, "sell")
                    if order3.status_code == 200:
                        print(
                            "Done (type 1) {}: {} {}: {} {} {}".format(
                                self.pairA, pairA, self.pairB, pairB, self.pairC, pairC
                            )
                        )
                        print("Spread: +{}".format(spread * 100))
                    else:
                        self.post_Alpaca_order(symbolC, BUY_C, "sell")
                        print("Bad Order 3")
                        print(f"Order 3: {order3}")
                        exit()
                else:
                    self.post_Alpaca_order(symbolB, BUY_B, "sell")
                    print("Bad Order 2")
                    exit()
            else:
                print("Bad Order 1")
                exit()

        # when ETH/USD is cheaper
        elif DIV < pairC * (1 - self.min_arb_percent / 100):
            order1 = self.post_Alpaca_order(symbolA, BUY_A, "buy")
            print(f"Order1: {order1}")
            if order1.status_code == 200:
                order2 = self.post_Alpaca_order(symbolC, BUY_A, "sell")
                print(f"Order2: {order2}")
                if order2.status_code == 200:
                    order3 = self.post_Alpaca_order(symbolB, SELL_C, "sell")
                    if order3.status_code == 200:
                        print(
                            "Done (type 2) {}: {} {}: {} {} {}".format(
                                self.pairA, pairA, self.pairB, pairB, self.pairC, pairC
                            )
                        )
                        print("Spread: -{}".format(spread * 100))
                    else:
                        self.post_Alpaca_order(symbolC, SELL_C, "buy")
                        print("Bad Order 3")
                        exit()
                else:
                    self.post_Alpaca_order(symbolA, BUY_A, "sell")
                    print("Bad Order 2")
                    print(f"Order2: {order2}")
                    exit()
            else:
                print("Bad order 1")
                exit()
        else:
            print("No arb opportunity, spread: {}".format(spread * 100))
            self.spreads.append(spread)

    def post_Alpaca_order(self, symbol, qty, side):
        """
        Post an order to Alpaca
        """
        try:
            order = requests.post(
                "{0}/v2/orders".format(ALPACA_BASE_URL),
                headers=HEADERS,
                json={
                    "symbol": symbol,
                    "qty": qty,
                    "side": side,
                    "type": "market",
                    "time_in_force": "gtc",
                },
            )
            return order
        except Exception as e:
            print("There was an issue posting order to Alpaca: {0}".format(e))
            return False
