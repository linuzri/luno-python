import os
import json
import time
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
print(f"API_KEY: {API_KEY}")
print(f"API_SECRET: {API_SECRET}")

if not API_KEY or not API_SECRET:
    raise ValueError("LUNO_API_KEY and LUNO_API_SECRET must be set in config.json")

client = LunoAPIClient(API_KEY, API_SECRET)

def get_tickers():
    try:
        res = client.get_tickers()
        tickers = res['tickers']
        table = [[ticker['pair'], ticker['last_trade'], ticker['bid'], ticker['ask'], ticker.get('volume', 'N/A')] for ticker in tickers]
        headers = ["Pair", "Last Trade", "Bid", "Ask", "Volume"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error getting tickers: {e}")
    time.sleep(0.5)

def get_ticker(pair):
    try:
        res = client.get_ticker(pair)
        print(res)
    except Exception as e:
        print(f"Error getting ticker: {e}")
    time.sleep(0.5)

def get_order_book(pair):
    try:
        res = client.get_order_book(pair)
        print(res)
    except Exception as e:
        print(f"Error getting order book: {e}")
    time.sleep(0.5)

def list_trades(pair, since):
    try:
        res = client.list_trades(pair, since)
        print(res)
    except Exception as e:
        print(f"Error listing trades: {e}")
    time.sleep(0.5)

def get_candles(pair, since, duration):
    try:
        res = client.get_candles(pair, since, duration)
        print(res)
    except Exception as e:
        print(f"Error getting candles: {e}")
    time.sleep(0.5)

def get_balances():
    res = None  # Initialize res to None
    try:
        res = client.get_balances()
        print(res)
    except Exception as e:
        print(f"Error getting balances: {e}")
    time.sleep(0.5)
    return res

def list_transactions(account_id):
    try:
        res = client.list_transactions(account_id)
        print(res)
    except Exception as e:
        print(f"Error listing transactions: {e}")
    time.sleep(0.5)

def list_pending_transactions(account_id):
    try:
        res = client.list_pending_transactions(account_id)
        print(res)
    except Exception as e:
        print(f"Error listing pending transactions: {e}")
    time.sleep(0.5)

def list_orders():
    try:
        res = client.list_orders()
        print(res)
    except Exception as e:
        print(f"Error listing orders: {e}")
    time.sleep(0.5)

def list_user_trades(pair):
    try:
        res = client.list_user_trades(pair)
        print(res)
    except Exception as e:
        print(f"Error listing user trades: {e}")
    time.sleep(0.5)

def get_fee_info(pair):
    try:
        res = client.get_fee_info(pair)
        print(res)
    except Exception as e:
        print(f"Error getting fee info: {e}")
    time.sleep(0.5)

def get_funding_address(asset):
    try:
        res = client.get_funding_address(asset)
        print(res)
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

def get_valid_timestamp(prompt):
    while True:
        try:
            timestamp = int(input(prompt))
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
            pair = input("Enter pair: ")
            get_ticker(pair)
        elif choice == '3':
            pair = input("Enter pair: ")
            get_order_book(pair)
        elif choice == '4':
            pair = input("Enter pair: ")
            since = get_valid_timestamp("Enter since timestamp: ")
            list_trades(pair, since)
        elif choice == '5':
            pair = input("Enter pair: ")
            since = get_valid_timestamp("Enter since timestamp: ")
            duration = get_valid_timestamp("Enter duration: ")
            get_candles(pair, since, duration)
        elif choice == '6':
            get_balances()
        elif choice == '7':
            account_id = input("Enter account ID: ")
            list_transactions(account_id)
        elif choice == '8':
            account_id = input("Enter account ID: ")
            list_pending_transactions(account_id)
        elif choice == '9':
            list_orders()
        elif choice == '10':
            pair = input("Enter pair: ")
            list_user_trades(pair)
        elif choice == '11':
            pair = input("Enter pair: ")
            get_fee_info(pair)
        elif choice == '12':
            asset = input("Enter asset: ")
            get_funding_address(asset)
        elif choice == '13':
            test_api_call()
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
