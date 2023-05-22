"""
Script for fetching Epic-Cash blockchain and market data using public APIs
"""

from json import JSONDecodeError
from decimal import Decimal
from typing import Union
import socket
import json

import requests

from .cache import cache


CACHE_FILE = ".cache"


class MarketData:
    """
    Helper class to fetch market data from public API's,
    needed for currency calculations.
    """
    btc_feed_url = "https://blockchain.info"
    epic_feed_url = "https://api.coingecko.com/api/v3"

    @cache(ttl=60*3)
    def price_epic_vs(self, currency: str):
        symbol = currency.upper()
        if len(symbol) == 3:
            try:
                url = f"{self.epic_feed_url}/simple/price?ids=epic-cash&vs_currencies={symbol}"
                data = json.loads(requests.get(url).content)
                return Decimal(data['epic-cash'][symbol.lower()])
            except JSONDecodeError as er:
                print(er)
                return 0

    @cache(ttl=60*3)
    def price_btc_vs(self, currency: str):
        symbol = currency.upper()
        if len(symbol) == 3:
            try:
                url = f"{self.btc_feed_url}/ticker"
                data = json.loads(requests.get(url).content)
                return Decimal(data[symbol]['last'])
            except JSONDecodeError as er:
                print(er)
                return 0

    def get(self, currency: str):
        return {'epic_price': self.price_epic_vs(currency),
                'btc_price': self.price_btc_vs(currency),
                'symbol': currency.upper()}

    @cache(ttl=60*5)
    def currency_to_btc(self, value: Union[Decimal, float, int], currency: str):
        """Find bitcoin price in given currency"""
        symbol = currency.upper()
        if len(symbol) == 3:
            try:
                url = f'{self.btc_feed_url}/tobtc?currency={currency}&value={value}'
                data = json.loads(requests.get(url).content)
                return Decimal(data)
            except JSONDecodeError as er:
                print(er)
                return 0


class BlockchainData:
    """
    Database handler connected to epic-radar.com API,
    needed for Blockchain state data
    """
    API_URL = "https://epic-radar.com/api/"
    API_GET_BLOCKS = "explorer/blocks/"
    STRATUM_HOST = "209.127.178.120"
    STRATUM_PORT = 3416

    def _connect_to_stratum(self, payload: bytes):
        """
        Connect to the node stratum server and fetch most recent block data
        """
        to_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        to_server_socket.connect((self.STRATUM_HOST, self.STRATUM_PORT))
        try:
            to_server_socket.send(payload)

            server_data = to_server_socket.recv(4024)
            return json.loads(server_data)
        except ConnectionResetError:
            return None

    @cache(ttl=60)
    def get_live_block(self):
        payload = b'{"id":"0","jsonrpc":"2.0","method":"getjobtemplate",' \
                  b'"params":{"algorithm":"progpow"}}'
        data = self._connect_to_stratum(payload=payload)

        if data:
            del data['params']['difficulty']
            del data['params']['pre_pow']
            del data['params']['epochs']

            return data['params']

    @cache(ttl=60)
    def get_last_block(self):
        response = requests.get(f"{self.API_URL}{self.API_GET_BLOCKS}")
        blocks = response.json()
        return blocks['results'][0]
