import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API key and secret from config.json
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)
    API_KEY = config.get('luno_api_key')
    API_SECRET = config.get('luno_api_secret')

class LunoAPIClient:
    BASE_URL = "https://api.luno.com"

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def _request(self, method, endpoint, params=None):
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(method, url, auth=(self.api_key, self.api_secret), params=params)
        if response.status_code != 200:
            raise Exception(f"API call failed: {response.status_code} {response.text}")
        return response.json()

    def get_tickers(self):
        return self._request("GET", "/api/1/tickers")

    def get_ticker(self, pair):
        return self._request("GET", "/api/1/ticker", params={"pair": pair})

    def get_order_book(self, pair):
        return self._request("GET", "/api/1/orderbook", params={"pair": pair})

    def list_trades(self, pair, since):
        return self._request("GET", "/api/1/trades", params={"pair": pair, "since": since})

    def get_candles(self, pair, since, duration):
        return self._request("GET", "/api/exchange/1/candles", params={"pair": pair, "since": since, "duration": duration})

    def get_balances(self):
        return self._request("GET", "/api/1/balance")

    def list_transactions(self, account_id):
        return self._request("GET", f"/api/1/accounts/{account_id}/transactions", params={"min_row": 1, "max_row": 10})

    def list_pending_transactions(self, account_id):
        return self._request("GET", f"/api/1/accounts/{account_id}/pending")

    def list_orders(self):
        return self._request("GET", "/api/1/listorders")

    def list_user_trades(self, pair):
        return self._request("GET", "/api/1/listtrades", params={"pair": pair})

    def get_fee_info(self, pair):
        return self._request("GET", "/api/1/fee_info", params={"pair": pair})

    def get_funding_address(self, asset):
        return self._request("GET", "/api/1/funding_address", params={"asset": asset})

    def create_account(self, currency, name):
        return self._request("POST", "/api/1/accounts", params={"currency": currency, "name": name})

    def update_account_name(self, account_id, name):
        return self._request("PUT", f"/api/1/accounts/{account_id}/name", params={"name": name})

    def validate_address(self, address, currency):
        return self._request("POST", "/api/1/address/validate", params={"address": address, "currency": currency})

    def send(self, amount, currency, address, description=None, message=None):
        params = {
            "amount": amount,
            "currency": currency,
            "address": address,
            "description": description,
            "message": message
        }
        return self._request("POST", "/api/1/send", params=params)

    def list_withdrawals(self):
        return self._request("GET", "/api/1/withdrawals")

    def create_withdrawal(self, type, amount, beneficiary_id=None, fast=False):
        params = {
            "type": type,
            "amount": amount,
            "beneficiary_id": beneficiary_id,
            "fast": fast
        }
        return self._request("POST", "/api/1/withdrawals", params=params)

    def get_withdrawal(self, withdrawal_id):
        return self._request("GET", f"/api/1/withdrawals/{withdrawal_id}")

    def cancel_withdrawal(self, withdrawal_id):
        return self._request("DELETE", f"/api/1/withdrawals/{withdrawal_id}")
