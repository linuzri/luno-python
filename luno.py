import os
import json
import time
from datetime import datetime, timedelta
from luno_api_client import LunoAPIClient
from tabulate import tabulate
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API key and secret from config.json
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)
    API_KEY = config.get('luno_api_key')
    API_SECRET = config.get('luno_api_secret')

# Debug prints to verify API key and secret
#print(f"API_KEY: {API_KEY}")
#print(f"API_SECRET: {API_SECRET}")

# Retrieve default account ID from config.json
DEFAULT_ACCOUNT_ID = config.get('default_account_id')

# Debug print to verify default account ID
#print(f"DEFAULT_ACCOUNT_ID: {DEFAULT_ACCOUNT_ID}")

if not API_KEY or not API_SECRET:
    raise ValueError("LUNO_API_KEY and LUNO_API_SECRET must be set in config.json")

client = LunoAPIClient(API_KEY, API_SECRET)

# Set default pair and timestamp
DEFAULT_PAIR = "XBTMYR"
DEFAULT_TIMESTAMP = int(datetime.now().timestamp())

def get_tickers(pair=DEFAULT_PAIR):
    try:
        res = client.get_tickers()
        tickers = res['tickers']
        table = [[ticker['pair'], ticker['last_trade'], ticker['bid'], ticker['ask'], ticker.get('volume', 'N/A')] for ticker in tickers]
        headers = ["Pair", "Last Trade", "Bid", "Ask", "Volume"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error getting tickers: {e}")
    time.sleep(0.5)

def get_ticker(pair=DEFAULT_PAIR):
    try:
        res = client.get_ticker(pair)
        table = [[key, value] for key, value in res.items()]
        headers = ["Field", "Value"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error getting ticker: {e}")
    time.sleep(0.5)

def get_order_book(pair=DEFAULT_PAIR):
    try:
        res = client.get_order_book(pair)
        bids = res.get('bids', [])
        asks = res.get('asks', [])
        table = [["Bid", bid['price'], bid['volume']] for bid in bids] + [["Ask", ask['price'], ask['volume']] for ask in asks]
        headers = ["Type", "Price", "Volume"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error getting order book: {e}")
    time.sleep(0.5)

def list_trades(pair=DEFAULT_PAIR, since=None):
    if since is None:
        since = int((datetime.now() - timedelta(hours=24)).timestamp())
    try:
        res = client.list_trades(pair, since)
        trades = res.get('trades', [])
        if trades is None:
            trades = []
        table = [[trade['timestamp'], trade['price'], trade['volume'], trade['is_buy']] for trade in trades]
        headers = ["Timestamp", "Price", "Volume", "Is Buy"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error listing trades: {e}")
    time.sleep(0.5)

def get_candles(pair=DEFAULT_PAIR, since=DEFAULT_TIMESTAMP, duration=3600):
    try:
        res = client.get_candles(pair, since, duration)
        candles = res.get('candles', [])
        table = [[candle['timestamp'], candle['open'], candle['close'], candle['high'], candle['low'], candle['volume']] for candle in candles]
        headers = ["Timestamp", "Open", "Close", "High", "Low", "Volume"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error getting candles: {e}")
    time.sleep(0.5)

def get_balances():
    res = None  # Initialize res to None
    try:
        res = client.get_balances()
        balances = res.get('balance', [])
        table = [[balance['account_id'], balance['asset'], balance['balance'], balance['reserved'], balance['unconfirmed']] for balance in balances]
        headers = ["Account ID", "Asset", "Balance", "Reserved", "Unconfirmed"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error getting balances: {e}")
    time.sleep(0.5)
    return res

def list_transactions(account_id=DEFAULT_ACCOUNT_ID):
    try:
        res = client.list_transactions(account_id)
        transactions = res.get('transactions', [])
        if transactions is None:
            transactions = []
        table = [[transaction['timestamp'], transaction['balance'], transaction['available'], transaction['description']] for transaction in transactions]
        headers = ["Timestamp", "Balance", "Available", "Description"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error listing transactions: {e}")
    time.sleep(0.5)

def list_pending_transactions(account_id=DEFAULT_ACCOUNT_ID):
    try:
        res = client.list_pending_transactions(account_id)
        transactions = res.get('transactions', [])
        table = [[transaction['timestamp'], transaction['balance'], transaction['available'], transaction['description']] for transaction in transactions]
        headers = ["Timestamp", "Balance", "Available", "Description"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error listing pending transactions: {e}")
    time.sleep(0.5)

def list_orders():
    try:
        res = client.list_orders()
        orders = res.get('orders', [])
        table = [[order['order_id'], order['pair'], order['type'], order['state'], order.get('price', 'N/A'), order.get('volume', 'N/A')] for order in orders]
        headers = ["Order ID", "Pair", "Type", "State", "Price", "Volume"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception:
        pass  # Handle the exception without displaying an error message
    time.sleep(0.5)

def list_user_trades(pair=DEFAULT_PAIR):
    try:
        res = client.list_user_trades(pair)
        trades = res.get('trades', [])
        table = [[trade['timestamp'], trade['price'], trade['volume'], trade['fee_base'], trade['fee_counter']] for trade in trades]
        headers = ["Timestamp", "Price", "Volume", "Fee Base", "Fee Counter"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error listing user trades: {e}")
    time.sleep(0.5)

def get_fee_info(pair=DEFAULT_PAIR):
    try:
        res = client.get_fee_info(pair)
        table = [[key, value] for key, value in res.items()]
        headers = ["Field", "Value"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error getting fee info: {e}")
    time.sleep(0.5)

def get_funding_address(asset=DEFAULT_PAIR):
    try:
        res = client.get_funding_address(asset)
        table = [[key, value] for key, value in res.items()]
        headers = ["Field", "Value"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error getting funding address: {e}")
    time.sleep(0.5)

def test_api_call():
    try:
        res = client.get_tickers()
        print("API call successful. Status: OK")
    except Exception as e:
        print(f"API call failed. Error: {e}")

def menu():
    print("Select an option:")
    print("1. Get Tickers")
    print("2. Get Ticker")
    print("3. Get Order Book")
    print("4. List Trades")
    print("5. Get Candles")
    print("6. Get Balances")
    print("7. List Transactions")
    print("8. List Pending Transactions")
    print("9. List Orders")
    print("10. List User Trades")
    print("11. Get Fee Info")
    print("12. Get Funding Address")
    print("13. Test API Call")
    print("0. Exit")
    return input("Enter your choice: ")

def get_valid_timestamp(prompt, default=None):
    while True:
        try:
            user_input = input(prompt)
            if user_input == "" and default is not None:
                return default
            timestamp = int(user_input)
            return timestamp
        except ValueError:
            print("Invalid input. Please enter a valid integer timestamp.")

def main():
    try:
        test_api_call()  # Test the API call to ensure the client is set up correctly
    except Exception as e:
        print(f"Failed to initialize client: {e}")
        return
    
    while True:
        choice = menu()
        if choice == '1':
            get_tickers()
        elif choice == '2':
            pair = input(f"Enter pair (default: {DEFAULT_PAIR}): ") or DEFAULT_PAIR
            get_ticker(pair)
        elif choice == '3':
            pair = input(f"Enter pair (default: {DEFAULT_PAIR}): ") or DEFAULT_PAIR
            get_order_book(pair)
        elif choice == '4':
            pair = input(f"Enter pair (default: {DEFAULT_PAIR}): ") or DEFAULT_PAIR
            since = get_valid_timestamp("Enter timestamp (default: 1740312918074): ", 1740312918074)
            list_trades(pair, since)
        elif choice == '5':
            pair = input(f"Enter pair (default: {DEFAULT_PAIR}): ") or DEFAULT_PAIR
            get_candles(pair)
        elif choice == '6':
            get_balances()
        elif choice == '7':
            account_id = input(f"Enter account ID (default: {DEFAULT_ACCOUNT_ID}): ") or DEFAULT_ACCOUNT_ID
            list_transactions(account_id)
        elif choice == '8':
            account_id = input(f"Enter account ID (default: {DEFAULT_ACCOUNT_ID}): ") or DEFAULT_ACCOUNT_ID
            list_pending_transactions(account_id)
        elif choice == '9':
            list_orders()
        elif choice == '10':
            pair = input(f"Enter pair (default: {DEFAULT_PAIR}): ") or DEFAULT_PAIR
            list_user_trades(pair)
        elif choice == '11':
            pair = input(f"Enter pair (default: {DEFAULT_PAIR}): ") or DEFAULT_PAIR
            get_fee_info(pair)
        elif choice == '12':
            asset = input(f"Enter asset (default: {DEFAULT_PAIR}): ") or DEFAULT_PAIR
            get_funding_address(asset)
        elif choice == '13':
            test_api_call()
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
