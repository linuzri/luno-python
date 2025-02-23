import json
import os
import time
from luno_python.client import Client

config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)
    API_KEY = config['luno_api_key']
    API_SECRET = config['luno_api_secret']

if not API_KEY or not API_SECRET:
    raise ValueError("API key and secret must be set in config.json")


def get_tickers(client):
    try:
        res = client.get_tickers()
        print("\nCurrent Tickers:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching tickers: {e}")

def get_ticker(client, pair):
    try:
        res = client.get_ticker(pair=pair)
        print(f"\nTicker for {pair}:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching ticker: {e}")

def get_order_book(client, pair):
    try:
        res = client.get_order_book(pair=pair)
        print(f"\nOrder Book for {pair}:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching order book: {e}")

def list_trades(client, pair, since):
    try:
        res = client.list_trades(pair=pair, since=since)
        print(f"\nRecent Trades for {pair}:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching trades: {e}")

def get_candles(client, pair, since, duration):
    try:
        res = client.get_candles(pair=pair, since=since, duration=duration)
        print(f"\nCandles for {pair}:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching candles: {e}")

def get_balances(client):
    try:
        res = client.get_balances()
        print("\nAccount Balances:")
        print(res)
        time.sleep(0.5)
        return res
    except Exception as e:
        print(f"Error fetching balances: {e}")
        return None

def list_transactions(client, account_id):
    try:
        res = client.list_transactions(id=account_id, min_row=1, max_row=10)
        print("\nRecent Transactions:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching transactions: {e}")

def list_pending_transactions(client, account_id):
    try:
        res = client.list_pending_transactions(id=account_id)
        print("\nPending Transactions:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching pending transactions: {e}")

def list_orders(client):
    try:
        res = client.list_orders()
        print("\nOpen Orders:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching orders: {e}")

def list_user_trades(client, pair):
    try:
        res = client.list_user_trades(pair=pair)
        print(f"\nUser Trades for {pair}:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching user trades: {e}")

def get_fee_info(client, pair):
    try:
        res = client.get_fee_info(pair=pair)
        print(f"\nFee Info for {pair}:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching fee info: {e}")

def get_funding_address(client, asset):
    try:
        res = client.get_funding_address(asset=asset)
        print(f"\nFunding Address for {asset}:")
        print(res)
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching funding address: {e}")

def test_api_connection(client):
    try:
        res = client.get_tickers()
        if res:
            print("\nAPI Connection Test Successful!")
            print("Response received from the server.")
        else:
            print("\nAPI Connection Test Failed.")
            print("No response received from the server.")
    except Exception as e:
        print(f"\nAPI Connection Test Failed: {e}")

def display_test_menu():
    print("\nAPI Testing Menu")
    print("-----------------")
    print("1. Test API Connection")
    print("2. Back to Main Menu")

def display_main_menu():
    print("\nLuno API Client - Main Menu")
    print("-------------------------------")
    print("1. Market Data")
    print("2. Account Management")
    print("3. Orders & Trades")
    print("4. Funding & Fees")
    print("5. Test API Connection")
    print("6. Exit Program")

def display_market_menu():
    print("\nMarket Data Menu")
    print("-------------------")
    print("1. Get All Tickers")
    print("2. Get Specific Ticker")
    print("3. Get Order Book")
    print("4. List Recent Trades")
    print("5. Get Candle Data")
    print("6. Back to Main Menu")

def display_account_menu():
    print("\nAccount Management Menu")
    print("-------------------------")
    print("1. Get Account Balances")
    print("2. List Transactions")
    print("3. List Pending Transactions")
    print("4. Back to Main Menu")

def display_orders_menu():
    print("\nOrders & Trades Menu")
    print("----------------------")
    print("1. List Open Orders")
    print("2. List User Trades")
    print("3. Back to Main Menu")

def display_funding_menu():
    print("\nFunding & Fees Menu")
    print("---------------------")
    print("1. Get Fee Info")
    print("2. Get Funding Address")
    print("3. Back to Main Menu")

def main():
    client = Client(api_key_id=API_KEY, api_key_secret=API_SECRET)
    
    while True:
        display_main_menu()
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            while True:
                display_market_menu()
                market_choice = input("Enter your choice (1-6): ")
                
                if market_choice == "1":
                    get_tickers(client)
                elif market_choice == "2":
                    pair = input("Enter trading pair (e.g., XBTZAR): ")
                    get_ticker(client, pair)
                elif market_choice == "3":
                    pair = input("Enter trading pair (e.g., XBTZAR): ")
                    get_order_book(client, pair)
                elif market_choice == "4":
                    pair = input("Enter trading pair (e.g., XBTZAR): ")
                    since = int(time.time()*1000) - 24*60*59*1000
                    list_trades(client, pair, since)
                elif market_choice == "5":
                    pair = input("Enter trading pair (e.g., XBTZAR): ")
                    since = int(time.time()*1000) - 24*60*59*1000
                    get_candles(client, pair, since, 300)
                elif market_choice == "6":
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
        elif choice == "2":
            while True:
                display_account_menu()
                account_choice = input("Enter your choice (1-4): ")
                
                if account_choice == "1":
                    balances = get_balances(client)
                    if balances and balances['balance']:
                        account_id = balances['balance'][0]['account_id']
                        list_transactions(client, account_id)
                        list_pending_transactions(client, account_id)
                elif account_choice == "2":
                    balances = get_balances(client)
                    if balances and balances['balance']:
                        account_id = balances['balance'][0]['account_id']
                        list_transactions(client, account_id)
                elif account_choice == "3":
                    balances = get_balances(client)
                    if balances and balances['balance']:
                        account_id = balances['balance'][0]['account_id']
                        list_pending_transactions(client, account_id)
                elif account_choice == "4":
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
        elif choice == "3":
            while True:
                display_orders_menu()
                orders_choice = input("Enter your choice (1-3): ")
                
                if orders_choice == "1":
                    list_orders(client)
                elif orders_choice == "2":
                    pair = input("Enter trading pair (e.g., XBTZAR): ")
                    list_user_trades(client, pair)
                elif orders_choice == "3":
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
        elif choice == "4":
            while True:
                display_funding_menu()
                funding_choice = input("Enter your choice (1-3): ")
                
                if funding_choice == "1":
                    pair = input("Enter trading pair (e.g., XBTZAR): ")
                    get_fee_info(client, pair)
                elif funding_choice == "2":
                    asset = input("Enter asset (e.g., XBT): ")
                    get_funding_address(client, asset)
                elif funding_choice == "3":
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
        elif choice == "5":
            while True:
                display_test_menu()
                test_choice = input("Enter your choice (1-2): ")
                
                if test_choice == "1":
                    test_api_connection(client)
                elif test_choice == "2":
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
        elif choice == "6":
            print("Exiting program. Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
