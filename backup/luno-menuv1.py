import json
import os
import time
from tabulate import tabulate
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
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["Pair", "Last Trade", "Bid", "Ask", "High", "Low", "Volume"]
            for ticker in res['tickers']:  # Access the 'tickers' key in response
                row = [
                    ticker['pair'],
                    ticker['last_trade'],
                    ticker['bid'],
                    ticker['ask'],
                    ticker['high'],
                    ticker['low'],
                    ticker['rolling_24_hour_volume']
                ]
                table.append(row)
            print("\nCurrent Tickers:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
        else:
            print("\nNo tickers found.")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching tickers: {e}")

def get_ticker(client, pair):
    try:
        res = client.get_ticker(pair=pair)
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["Pair", "last_trade", "bid", "bid_volume", "ask", "ask_volume"]
            row = [
                res['pair'],
                res['last_trade'],
                res['bid'],
                res['bid_volume'],
                res['ask'],
                res['ask_volume']
            ]
            table.append(row)
            print(f"\nTicker for {pair}:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
        else:
            print(f"\nNo ticker found for {pair}.")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching ticker: {e}")

def get_order_book(client, pair):
    try:
        res = client.get_order_book(pair=pair)
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["Type", "volume", "price"]
            for order in res['bids + asks']:
                row = [
                    order['type'],
                    order['volume'],
                    order['price']
                ]
                table.append(row)
            print(f"\nOrder Book for {pair}:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
        else:
            print(f"\nNo order book found for {pair}.")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching order book: {e}")

def list_trades(client, pair, since):
    try:
        res = client.list_trades(pair=pair, since=since)
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["timestamp", "price", "amount"]
            for trade in res:
                row = [
                    trade['timestamp'],
                    trade['price'],
                    trade['amount']
                ]
                table.append(row)
            print(f"\nRecent Trades for {pair}:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
        else:
            print(f"\nNo recent trades found for {pair}.")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching trades: {e}")

def get_candles(client, pair, since, duration):
    try:
        res = client.get_candles(pair=pair, since=since, duration=duration)
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["time", "open", "high", "low", "close", "volume"]
            for candle in res:
                row = [
                    candle['time'],
                    candle['open'],
                    candle['high'],
                    candle['low'],
                    candle['close'],
                    candle['volume']
                ]
                table.append(row)
            print(f"\nCandles for {pair}:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
        else:
            print(f"\nNo candles found for {pair}.")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching candles: {e}")

def get_balances(client):
    try:
        res = client.get_balances()
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["asset_class", "balance", "balance_available", "fee", "opening_balance", "running_balance"]
            for balance in res['balance']:
                row = [
                    balance['asset_class'],
                    balance['balance'],
                    balance['balance_available'],
                    balance['fee'],
                    balance['opening_balance'],
                    balance['running_balance']
                ]
                table.append(row)
            print("\nAccount Balances:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
            time.sleep(0.5)
            return res
        else:
            print("\nNo account balances found.")
            return None
    except Exception as e:
        print(f"Error fetching balances: {e}")
        return None

def list_transactions(client, account_id):
    try:
        res = client.list_transactions(id=account_id, min_row=1, max_row=10)
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["timestamp", "type", "amount", "fee", "fee_currency"]
            for transaction in res:
                row = [
                    transaction['timestamp'],
                    transaction['type'],
                    transaction['amount'],
                    transaction['fee'],
                    transaction['fee_currency']
                ]
                table.append(row)
            print("\nRecent Transactions:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
            time.sleep(0.5)
        else:
            print("\nNo recent transactions found.")
    except Exception as e:
        print(f"Error fetching transactions: {e}")

def list_pending_transactions(client, account_id):
    try:
        res = client.list_pending_transactions(id=account_id)
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["timestamp", "type", "amount", "fee", "fee_currency"]
            for transaction in res:
                row = [
                    transaction['timestamp'],
                    transaction['type'],
                    transaction['amount'],
                    transaction['fee'],
                    transaction['fee_currency']
                ]
                table.append(row)
            print("\nPending Transactions:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
            time.sleep(0.5)
        else:
            print("\nNo pending transactions found.")
    except Exception as e:
        print(f"Error fetching pending transactions: {e}")

def list_orders(client):
    try:
        res = client.list_orders()
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["order_id", "pair", "type", "type", "volume", "remaining", "price", "created_at"]
            for order in res:
                row = [
                    order['order_id'],
                    order['pair'],
                    order['type'],
                    order['volume'],
                    order['remaining'],
                    order['price'],
                    order['created_at']
                ]
                table.append(row)
            print("\nOpen Orders:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
            time.sleep(0.5)
        else:
            print("\nNo open orders found.")
    except Exception as e:
        print(f"Error fetching orders: {e}")

def list_user_trades(client, pair):
    try:
        res = client.list_user_trades(pair=pair)
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["timestamp", "price", "amount"]
            for trade in res:
                row = [
                    trade['timestamp'],
                    trade['price'],
                    trade['amount']
                ]
                table.append(row)
            print(f"\nUser Trades for {pair}:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
            time.sleep(0.5)
        else:
            print(f"\nNo user trades found for {pair}.")
    except Exception as e:
        print(f"Error fetching user trades: {e}")

def get_fee_info(client, pair):
    try:
        # Ensure pair is uppercase
        pair = pair.upper()
        res = client.get_fee_info(pair=pair)
        if res and 'maker_fee' in res:
            table = []
            headers = ["Maker Fee", "Taker Fee"]
            row = [
                res['maker_fee'],
                res['taker_fee']
            ]
            table.append(row)
            print(f"\nFee Info for {pair}:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
        else:
            print(f"\nNo fee info found for {pair}. Please check if the trading pair is valid.")
        time.sleep(0.5)
    except Exception as e:
        print(f"Error fetching fee info: {e}")
        print("Please verify your API credentials and trading pair")

def get_funding_address(client, asset):
    try:
        res = client.get_funding_address(asset=asset)
        if res:
            # Extract the relevant fields from the response
            table = []
            headers = ["address", "address_tag"]
            row = [
                res['address'],
                res['address_tag']
            ]
            table.append(row)
            print(f"\nFunding Address for {asset}:")
            print(tabulate(table, headers, tablefmt="fancy_grid"))
            time.sleep(0.5)
        else:
            print(f"\nNo funding address found for {asset}.")
    except Exception as e:
        print(f"Error fetching funding address: {e}")

def test_api_connection(client):
    try:
        res = client.get_tickers()
        if res:
            print("\nAPI Connection test successful!")
        else:
            print("\nAPI Connection test failed.")
    except Exception as e:
        print(f"\nAPI Connection test failed: {e}")

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
    # Reinitialize the client with proper API settings
    client = Client(api_key_id=API_KEY, 
                   api_key_secret=API_SECRET,
                   base_url='https://api.luno.com/api/1')  # Add explicit base URL
    
    # Add a quick validation test
    try:
        test_api_connection(client)
    except Exception as e:
        print(f"Failed to initialize API connection: {e}")
        print("Please check your API credentials in config.json")
        return
    
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
                    pair = input("Enter trading pair (e.g., XLMZAR): ")
                    get_ticker(client, pair)
                elif market_choice == "3":
                    pair = input("Enter trading pair (e.g., XLMZAR): ")
                    get_order_book(client, pair)
                elif market_choice == "4":
                    pair = input("Enter trading pair (e.g., XLMZAR): ")
                    since = int(time.time()*1000) - 24*60*60*1000
                    list_trades(client, pair, since)
                elif market_choice == "5":
                    pair = input("Enter trading pair (e.g., XLMZAR): ")
                    since = int(time.time()*1000) - 24*60*60*1000
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
                    pair = input("Enter trading pair (e.g., XLMZAR): ")
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
                    pair = input("Enter trading pair (e.g., XLMZAR): ")
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
