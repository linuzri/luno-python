import os
import json
import time
from datetime import datetime, timedelta
from luno_api_client import LunoAPIClient
from tabulate import tabulate
from dotenv import load_dotenv
from termcolor import colored

# Load environment variables from .env file
load_dotenv()

# Retrieve API key and secret from config.json
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)
    API_KEY = config.get('luno_api_key')
    API_SECRET = config.get('luno_api_secret')

# Retrieve default account ID from config.json
DEFAULT_ACCOUNT_ID = config.get('default_account_id')

if not API_KEY or not API_SECRET:
    raise ValueError("LUNO_API_KEY and LUNO_API_SECRET must be set in config.json")

client = LunoAPIClient(API_KEY, API_SECRET)

# Set default pair
DEFAULT_PAIR = "XBTMYR"

def get_ticker(pair=DEFAULT_PAIR):
    try:
        res = client.get_ticker(pair)
        return res
    except Exception as e:
        print(f"Error getting ticker: {e}")
        return None
    time.sleep(0.5)

def start_fixed_amount_trading(initial_fund):
    """
    Trading strategy with fixed amount profit/loss thresholds:
    - Take profit when profit reaches MYR 10
    - Cut loss when loss reaches MYR 5
    """
    fund = initial_fund
    bought_price = None
    total_profit = 0
    total_loss = 0
    btc_bought = 0
    trade_status = "LOOKING_TO_BUY"  # Initial status
    
    # Fixed amount thresholds
    PROFIT_THRESHOLD = 10  # MYR
    LOSS_THRESHOLD = 5     # MYR
    
    print(f"Starting trading with {initial_fund} MYR")
    print(f"Profit target: {PROFIT_THRESHOLD} MYR per trade")
    print(f"Loss limit: {LOSS_THRESHOLD} MYR per trade")
    print("-" * 50)

    # Execute the first buy immediately using the provided fund
    try:
        ticker_data = get_ticker("XBTMYR")
        if not ticker_data:
            print("Failed to get ticker data. Exiting.")
            return
            
        last_trade_price = float(ticker_data['last_trade'])
        buy_price = last_trade_price * 1.006  # Including fee
        
        if fund >= buy_price:
            trade_status = "BUYING"
            print(colored(f"CURRENT STATUS: {trade_status}", "green", attrs=["bold"]))
            
            bought_price = last_trade_price
            btc_bought = buy_price / last_trade_price
            fund -= buy_price
            
            print(f"Initial Buy: Used {buy_price:.2f} MYR to buy {btc_bought:.8f} BTC at {bought_price:.2f} MYR")
            print(f"Remaining Fund: {fund:.2f} MYR")
            
            trade_status = "HOLDING"
        else:
            print(f"Insufficient funds for initial buy. Need {buy_price:.2f} MYR but have {fund:.2f} MYR")
            return
    except Exception as e:
        print(f"Error during initial buy: {e}")
        return

    # Add this function to create a more prominent status display
    def print_status_header(price, status):
        print("\n" + "=" * 60)
        print(f"| {'MARKET PRICE':^25} | {'TRADING STATUS':^28} |")
        print(f"| {f'{price:.2f} MYR':^25} | {status:^28} |")
        print("=" * 60)

    try:
        while True:
            # Clear the screen (works on most terminals)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Get current time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            ticker_data = get_ticker("XBTMYR")
            if not ticker_data:
                print("Failed to get ticker data. Retrying...")
                time.sleep(5)
                continue
                
            last_trade_price = float(ticker_data['last_trade'])
            
            # Print status header with timestamp
            print("\n" + "=" * 70)
            print(f"| {'TRADING BOT STATUS':^66} |")
            print(f"| {'Last Updated: ' + current_time:^66} |")
            print("=" * 70)
            print(f"| {'MARKET PRICE':^32} | {'TRADING STATUS':^33} |")
            print(f"| {f'{last_trade_price:.2f} MYR':^32} | {colored(trade_status, 'cyan', attrs=['bold']):^33} |")
            print("=" * 70)
            
            # Position information
            print("\nPOSITION DETAILS:")
            if bought_price is not None:
                position_value = btc_bought * last_trade_price
                unrealized_profit = position_value - (btc_bought * bought_price)
                profit_percent = (unrealized_profit / (btc_bought * bought_price)) * 100
                
                print(f"Entry Price: {bought_price:.2f} MYR")
                print(f"Current Position: {btc_bought:.8f} BTC (≈ {position_value:.2f} MYR)")
                
                if unrealized_profit >= 0:
                    print(colored(f"Unrealized Profit: {unrealized_profit:.2f} MYR (+{profit_percent:.2f}%)", "green"))
                    print(f"Profit Target: {PROFIT_THRESHOLD:.2f} MYR | Progress: {(unrealized_profit/PROFIT_THRESHOLD)*100:.1f}%")
                else:
                    print(colored(f"Unrealized Loss: {abs(unrealized_profit):.2f} MYR ({profit_percent:.2f}%)", "red"))
                    print(f"Loss Limit: {LOSS_THRESHOLD:.2f} MYR | Progress: {(abs(unrealized_profit)/LOSS_THRESHOLD)*100:.1f}%")
            else:
                print(colored("No active position", "yellow"))
                print(f"Available Funds: {fund:.2f} MYR")
                if fund > 0:
                    print(f"Looking for next buy opportunity...")
                else:
                    print(colored("Insufficient funds for trading", "red"))
            
            # Trading summary
            print("\nTRADING SUMMARY:")
            print(f"Initial Fund: {initial_fund:.2f} MYR")
            print(f"Current Fund: {fund:.2f} MYR")
            print(colored(f"Total Profit: {total_profit:.2f} MYR", "green"))
            print(colored(f"Total Loss: {total_loss:.2f} MYR", "red"))
            net_pl = total_profit - total_loss
            print(colored(f"Net P/L: {net_pl:.2f} MYR ({((net_pl)/initial_fund)*100:.2f}%)", 
                  "green" if net_pl >= 0 else "red"))
            
            # Instructions
            print("\n" + "-" * 70)
            print("Press Ctrl+C to exit trading bot")
            print(f"Next update in 5 seconds...")
            print("-" * 70)
            
            # Process trading logic (same as before)
            if bought_price is not None:
                # Check profit/loss thresholds and execute sells
                if unrealized_profit >= PROFIT_THRESHOLD:
                    trade_status = "SELLING (PROFIT TARGET)"
                    print(colored(f"CURRENT STATUS: {trade_status}", "green", attrs=["bold"]))
                    
                    sell_price = last_trade_price * 0.994  # Including fee
                    fund += sell_price * btc_bought
                    profit = unrealized_profit
                    total_profit += profit
                    
                    print(colored(f"PROFIT TARGET REACHED: {profit:.2f} MYR", "green", attrs=["bold"]))
                    print(f"Sold {btc_bought:.8f} BTC at {last_trade_price:.2f} MYR")
                    print(f"Fund after sell: {fund:.2f} MYR")
                    
                    bought_price = None
                    btc_bought = 0
                    trade_status = "LOOKING_TO_BUY"
                elif abs(unrealized_profit) >= LOSS_THRESHOLD and unrealized_profit < 0:
                    trade_status = "SELLING (STOP LOSS)"
                    print(colored(f"CURRENT STATUS: {trade_status}", "red", attrs=["bold"]))
                    
                    sell_price = last_trade_price * 0.994  # Including fee
                    fund += sell_price * btc_bought
                    loss = abs(unrealized_profit)
                    total_loss += loss
                    
                    print(colored(f"LOSS LIMIT REACHED: {loss:.2f} MYR", "red", attrs=["bold"]))
                    print(f"Sold {btc_bought:.8f} BTC at {last_trade_price:.2f} MYR to cut losses")
                    print(f"Fund after sell: {fund:.2f} MYR")
                    
                    bought_price = None
                    btc_bought = 0
                    trade_status = "LOOKING_TO_BUY"
            elif fund > 0:
                buy_price = last_trade_price * 1.006  # Including fee
                if fund >= buy_price:
                    trade_status = "BUYING"
                    print(colored(f"CURRENT STATUS: {trade_status}", "green", attrs=["bold"]))
                    
                    # Simple strategy: buy when we have funds available
                    bought_price = last_trade_price
                    max_btc_to_buy = fund / buy_price
                    btc_bought = max_btc_to_buy * 0.95  # Use 95% of available funds
                    actual_cost = btc_bought * buy_price
                    fund -= actual_cost
                    
                    print(colored(f"BUY: {btc_bought:.8f} BTC at {bought_price:.2f} MYR", "green"))
                    print(f"Cost: {actual_cost:.2f} MYR")
                    print(f"Remaining fund: {fund:.2f} MYR")
                    
                    trade_status = "HOLDING"
                else:
                    print(colored("Insufficient funds for next buy", "yellow"))

            # Wait before refreshing
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nTrading stopped by user.")
    except Exception as e:
        print(f"Error during trading: {e}")
    
    # Final summary
    print("\n" + "=" * 50)
    print("TRADING SESSION COMPLETED")
    print("=" * 50)
    print(f"Initial Fund: {initial_fund:.2f} MYR")
    print(f"Final Fund: {fund:.2f} MYR")
    print(colored(f"Total Profit: {total_profit:.2f} MYR", "green"))
    print(colored(f"Total Loss: {total_loss:.2f} MYR", "red"))
    net_pl = total_profit - total_loss
    print(colored(f"Net P/L: {net_pl:.2f} MYR", "green" if net_pl >= 0 else "red"))
    performance = ((fund - initial_fund) / initial_fund) * 100
    print(colored(f"Performance: {performance:.2f}%", "green" if performance >= 0 else "red"))
    print("=" * 50)

def menu():
    print("\n===== Fixed Amount Trading Bot =====")
    print("1. Start Trading (Fixed Amount Thresholds)")
    print("2. Test API Connection")
    print("0. Exit")
    return input("Enter your choice: ")

def test_api_call():
    try:
        res = client.get_tickers()
        print(colored("API call successful. Status: OK", "green"))
        return True
    except Exception as e:
        print(colored(f"API call failed. Error: {e}", "red"))
        return False

def main():
    # Test API connection first
    if not test_api_call():
        print(colored("Failed to connect to Luno API. Please check your credentials.", "red"))
        return
    
    while True:
        choice = menu()
        if choice == '1':
            try:
                initial_fund = float(input("Enter Initial Fund (MYR): "))
                if initial_fund <= 0:
                    print(colored("Initial fund must be greater than 0.", "red"))
                    continue
                start_fixed_amount_trading(initial_fund)
            except ValueError:
                print(colored("Please enter a valid number for the initial fund.", "red"))
        elif choice == '2':
            test_api_call()
        elif choice == '0':
            print(colored("Exiting...", "yellow"))
            break
        else:
            print(colored("Invalid choice. Please try again.", "red"))

if __name__ == '__main__':
    main() 