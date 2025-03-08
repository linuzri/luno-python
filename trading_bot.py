import os
import json
import time
from datetime import datetime
from luno_api_client import LunoAPIClient
from dotenv import load_dotenv
from tabulate import tabulate  # Import tabulate

# Ensure termcolor is installed
try:
    from termcolor import colored
except ImportError:
    import subprocess
    subprocess.check_call(["python", "-m", "pip", "install", "termcolor"])
    from termcolor import colored

# Load environment variables from .env file
load_dotenv()

# Retrieve API key and secret from config.json
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)
    API_KEY = config.get('luno_api_key')
    API_SECRET = config.get('luno_api_secret')

if not API_KEY or not API_SECRET:
    raise ValueError("LUNO_API_KEY and LUNO_API_SECRET must be set in config.json")

client = LunoAPIClient(API_KEY, API_SECRET)

DEFAULT_PAIR = "XBTMYR"

ACCOUNT_DETAILS_FILE = "account_details.json"

def save_account_details():
    global fund, bought_price, btc_bought, total_profit, total_loss, total_buy_amount, taker_fee
    account_details = {
        "fund": fund,
        "bought_price": bought_price,
        "btc_bought": btc_bought,
        "total_profit": total_profit,
        "total_loss": total_loss,
        "total_buy_amount": total_buy_amount,
        "taker_fee": taker_fee
    }
    with open(ACCOUNT_DETAILS_FILE, 'w') as f:
        json.dump(account_details, f)
    print("Account details saved.")

def load_account_details():
    global fund, bought_price, btc_bought, total_profit, total_loss, total_buy_amount, taker_fee
    if os.path.exists(ACCOUNT_DETAILS_FILE):
        with open(ACCOUNT_DETAILS_FILE, 'r') as f:
            account_details = json.load(f)
            fund = account_details.get("fund", 0)
            bought_price = account_details.get("bought_price", None)
            btc_bought = account_details.get("btc_bought", 0)
            total_profit = account_details.get("total_profit", 0)
            total_loss = account_details.get("total_loss", 0)
            total_buy_amount = account_details.get("total_buy_amount", 0)
            taker_fee = account_details.get("taker_fee", 0)
        print("Account details loaded.")
    else:
        print("No saved account details found. Starting with default values.")

def test_api_call():
    try:
        res = client.get_tickers()
        print(colored("API call successful. Status: OK", "green", attrs=["bold"]))
    except Exception as e:
        print(colored(f"API call failed. Error: {e}", "red", attrs=["bold"]))

def print_current_pair_price(pair=DEFAULT_PAIR):
    try:
        res = client.get_ticker(pair)
        last_trade_price = float(res['last_trade'])
        print(f"Current price for {pair}: {last_trade_price} MYR")
    except Exception as e:
        print(f"Error getting ticker: {e}")

def print_current_pair_price_continuously(pair=DEFAULT_PAIR):
    previous_price = None
    try:
        while True:
            res = client.get_ticker(pair)
            last_trade_price = float(res['last_trade'])
            if previous_price is not None:
                percentage_change = ((last_trade_price - previous_price) / previous_price) * 100
                if last_trade_price > previous_price:
                    price_text = colored(f"{last_trade_price} MYR (+{percentage_change:.2f}%)", "green", attrs=["bold"])
                elif last_trade_price < previous_price:
                    price_text = colored(f"{last_trade_price} MYR ({percentage_change:.2f}%)", "red", attrs=["bold"])
                else:
                    price_text = colored(f"{last_trade_price} MYR (0.00%)", "yellow", attrs=["bold"])
            else:
                price_text = colored(f"{last_trade_price} MYR", "yellow", attrs=["bold"])
            print(f"Current price for {pair}: {price_text}")
            previous_price = last_trade_price
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nStopped fetching prices. Returning to menu.")
    except Exception as e:
        print(f"Error getting ticker: {e}")

def start_trading_with_initial_fund():
    global fund, bought_price, btc_bought, total_buy_amount, taker_fee  # Declare global variables to store values
    try:
        initial_fund = float(input("Enter Initial Fund (MYR): "))
        res = client.get_ticker("XBTMYR")
        last_trade_price = float(res['last_trade'])
        fee_info = client.get_fee_info("XBTMYR")
        taker_fee = float(fee_info['taker_fee'])
        trading_fee_value = initial_fund * taker_fee
        btc_bought = (initial_fund * (1 - taker_fee)) / last_trade_price
        bought_price = last_trade_price
        fund = 0  # All funds are used in the initial buy
        total_buy_amount += initial_fund
        print(f"Used {initial_fund} MYR to buy {btc_bought} BTC at {last_trade_price} MYR")
        print(f"Buy Price: {last_trade_price} MYR, Unit XBTMYR: {btc_bought} BTC, Taker Fee: {taker_fee * 100}% ({trading_fee_value} MYR)")
    except Exception as e:
        print(f"Error during trading: {e}")

def show_trading_status():
    global fund, bought_price, btc_bought, total_buy_amount, taker_fee  # Use global variables to access stored values
    try:
        res = client.get_ticker("XBTMYR")
        last_trade_price = float(res['last_trade'])
        average_buying_price = total_buy_amount / btc_bought if btc_bought > 0 else 0
        trading_fee_value = total_buy_amount * taker_fee
        print(f"Current price for XBTMYR: {last_trade_price} MYR")
        print(f"Fund Balance: {fund} MYR")
        if bought_price is not None:
            print(f"Holding: {btc_bought} BTC")
            print(f"Buying Price: {bought_price} MYR")
            print(f"Average Buying Price: {average_buying_price} MYR")
            print(f"Taker Fee: {taker_fee * 100}% ({trading_fee_value} MYR)")
        else:
            print("No current holdings.")
        save_account_details()  # Save account details after showing status
    except Exception as e:
        print(f"Error getting trading status: {e}")

def add_fund():
    global fund  # Use global variable to update the fund
    try:
        additional_fund = float(input("Enter additional fund (MYR): "))
        fund += additional_fund
        print(f"Added {additional_fund} MYR to the account. New fund balance: {fund} MYR")
    except Exception as e:
        print(f"Error adding fund: {e}")

def buy_pair_with_fund():
    global fund, bought_price, btc_bought, total_buy_amount, taker_fee  # Use global variables to update holdings and fund status
    try:
        amount_to_use = float(input("Enter amount to use for buying (MYR): "))
        if amount_to_use > fund:
            print("Insufficient funds to execute the buy order.")
            return
        res = client.get_ticker("XBTMYR")
        last_trade_price = float(res['last_trade'])
        fee_info = client.get_fee_info("XBTMYR")
        taker_fee = float(fee_info['taker_fee'])
        trading_fee_value = amount_to_use * taker_fee
        btc_bought += (amount_to_use * (1 - taker_fee)) / last_trade_price
        bought_price = last_trade_price
        fund -= amount_to_use
        total_buy_amount += amount_to_use
        print(f"Used {amount_to_use} MYR to buy {(amount_to_use * (1 - taker_fee)) / last_trade_price} BTC at {last_trade_price} MYR")
        print(f"Buy Price: {last_trade_price} MYR, Unit XBTMYR: {btc_bought} BTC, Remaining Fund: {fund} MYR, Taker Fee: {taker_fee * 100}% ({trading_fee_value} MYR)")
    except Exception as e:
        print(f"Error during buying: {e}")

def sell_pair_with_fund():
    global fund, bought_price, btc_bought, taker_fee, total_profit, total_loss  # Use global variables to update holdings and fund status
    try:
        btc_to_sell = float(input("Enter amount to sell (BTC): "))
        if btc_to_sell > btc_bought:
            print("Insufficient BTC holdings to execute the sell order.")
            return
        res = client.get_ticker("XBTMYR")
        last_trade_price = float(res['last_trade'])
        amount_to_sell = btc_to_sell * last_trade_price
        trading_fee_value = amount_to_sell * taker_fee
        btc_bought -= btc_to_sell
        fund += amount_to_sell * (1 - taker_fee)  # Assuming a 0.6% fee for selling
        profit_loss = amount_to_sell * (1 - taker_fee) - (btc_to_sell * bought_price)
        if profit_loss > 0:
            total_profit += profit_loss
            print(colored(f"Sold {btc_to_sell} BTC for {amount_to_sell} MYR at {last_trade_price} MYR, Profit: {profit_loss:.2f} MYR", "green", attrs=["bold"]))
        else:
            total_loss += abs(profit_loss)
            print(colored(f"Sold {btc_to_sell} BTC for {amount_to_sell} MYR at {last_trade_price} MYR, Loss: {abs(profit_loss):.2f} MYR", "red", attrs=["bold"]))
        print(f"Sell Price: {last_trade_price} MYR, Unit XBTMYR: {btc_bought} BTC, Remaining Fund: {fund} MYR, Taker Fee: {taker_fee * 100}% ({trading_fee_value} MYR)")
    except Exception as e:
        print(f"Error during selling: {e}")

def show_profit():
    global total_profit, total_loss  # Use global variables to access profit and loss
    try:
        net_profit = total_profit - total_loss
        if net_profit > 0:
            print(colored(f"Net Profit: {net_profit:.2f} MYR", "green", attrs=["bold"]))
        else:
            print(colored(f"Net Loss: {abs(net_profit):.2f} MYR", "red", attrs=["bold"]))
    except Exception as e:
        print(f"Error showing profit: {e}")

def monitor_price():
    global total_buy_amount, btc_bought, taker_fee  # Use global variables to access average buy price
    try:
        total_events = btc_bought if btc_bought > 0 else 1
        average_buying_price = total_buy_amount / total_events
        while True:
            res = client.get_ticker("XBTMYR")
            last_trade_price = float(res['last_trade'])
            percentage_change = ((last_trade_price - average_buying_price) / average_buying_price) * 100 if average_buying_price > 0 else 0
            if last_trade_price > average_buying_price:
                alert_text = colored(f"Profit if Sell (Avg Buy Price: {average_buying_price} MYR, Change: {percentage_change:.2f}%)", "green", attrs=["bold"])
            elif last_trade_price == average_buying_price:
                alert_text = colored(f"No profit yet (Avg Buy Price: {average_buying_price} MYR, Change: {percentage_change:.2f}%)", "yellow", attrs=["bold"])
            else:
                alert_text = colored(f"Loss if Sell (Avg Buy Price: {average_buying_price} MYR, Change: {percentage_change:.2f}%)", "red", attrs=["bold"])
            print(f"Current price for XBTMYR: {last_trade_price} MYR - {alert_text}")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nStopped monitoring prices. Returning to menu.")
    except Exception as e:
        print(f"Error monitoring price: {e}")

def get_fee_info(pair=DEFAULT_PAIR):
    try:
        res = client.get_fee_info(pair)
        table = [[key, value] for key, value in res.items()]
        headers = ["Field", "Value"]
        print(tabulate(table, headers, tablefmt="pretty"))
    except Exception as e:
        print(f"Error getting fee info: {e}")
    time.sleep(0.5)

def run_trading_bot():
    global fund, bought_price, btc_bought, total_profit, total_loss, total_buy_amount, taker_fee  # Use global variables to track trading status
    try:
        fee_info = client.get_fee_info("XBTMYR")
        taker_fee = float(fee_info['taker_fee'])
        while True:
            res = client.get_ticker("XBTMYR")
            last_trade_price = float(res['last_trade'])
            print(f"Last trade price: {last_trade_price} MYR")

            if bought_price is not None:
                # Calculate the sell price including the fee and profit margin
                target_sell_price = bought_price * 1.02
                sell_price = target_sell_price * (1 - taker_fee)
                cut_loss_price = bought_price * 0.98

                current_value = btc_bought * last_trade_price
                profit_loss_value = current_value - (btc_bought * bought_price)
                profit_loss_percent = (profit_loss_value / (btc_bought * bought_price)) * 100

                if last_trade_price >= sell_price:
                    fund += sell_price
                    profit = sell_price - bought_price
                    total_profit += profit
                    print(colored(f"Sold XBT at {last_trade_price} MYR, Profit: {profit} MYR, Fund: {fund} MYR", "red", attrs=["bold"]))
                    bought_price = None
                elif last_trade_price <= cut_loss_price:
                    fund += last_trade_price * (1 - taker_fee)
                    loss = bought_price - last_trade_price
                    total_loss += loss
                    print(colored(f"Sold XBT at {last_trade_price} MYR to cut losses, Loss: {loss} MYR, Fund: {fund} MYR", "red", attrs=["bold"]))
                    bought_price = None
                else:
                    print(colored(f"Holding XBT at {last_trade_price} MYR, Profit/Loss: {profit_loss_value:.2f} MYR ({profit_loss_percent:.2f}%)", "yellow", attrs=["bold"]))

            if bought_price is None:
                # Execute the next buy
                buy_price = last_trade_price * 1.006
                trading_fee_value = buy_price * taker_fee
                if fund >= buy_price:
                    bought_price = last_trade_price
                    fund -= buy_price
                    btc_bought = (buy_price * (1 - taker_fee)) / last_trade_price
                    total_buy_amount += buy_price
                    print(colored(f"Bought {btc_bought} BTC at {bought_price} MYR, Used {buy_price} MYR, Remaining Fund: {fund} MYR, Taker Fee: {taker_fee * 100}% ({trading_fee_value} MYR)", "green", attrs=["bold"]))
                else:
                    print(colored(f"Holding fund, insufficient to buy at {last_trade_price} MYR", "yellow", attrs=["bold"]))

            print(f"Current Fund: {fund} MYR, Total Profit: {total_profit} MYR, Total Loss: {total_loss} MYR")
            time.sleep(5)  # Refresh every 5 seconds
    except KeyboardInterrupt:
        print("\nStopped trading bot. Returning to menu.")
    except Exception as e:
        print(f"Error during trading bot execution: {e}")

def reset_account():
    global fund, bought_price, btc_bought, total_profit, total_loss, total_buy_amount, taker_fee
    fund = 0
    bought_price = None
    btc_bought = 0
    total_profit = 0
    total_loss = 0
    total_buy_amount = 0
    taker_fee = 0
    save_account_details()
    print("Account details have been reset.")

def clear_screen():
    try:
        input("Press the spacebar to continue...")
    except KeyboardInterrupt:
        pass
    os.system('cls' if os.name == 'nt' else 'clear')

def menu():
    print(colored("================", "blue", attrs=["bold"]))
    print(colored("LUNO Trading App", "blue", attrs=["bold"]))
    print(colored("================", "blue", attrs=["bold"]))
    print("Select an option:")
    print("1. Test API")
    print(f"2. Live Price (default: {DEFAULT_PAIR})")
    print("3. Add Fund")
    print("4. Buy Assets")
    print("5. Show Account Details")
    # print("6. Start Trading")  # Disabled
    print("6. Sell Pair with Fund")
    print("7. Show Profit/Loss")
    print("8. Monitor Price")
    print("9. Get Fee Info")
    print("10. Reset Account")
    print("88. Run Trading Bot")
    print("0. Exit")
    return input("Enter your choice: ")

def main():
    global fund, bought_price, btc_bought, total_profit, total_loss, total_buy_amount, taker_fee  # Declare global variables to be used in show_trading_status
    fund = 0
    bought_price = None
    btc_bought = 0
    total_profit = 0
    total_loss = 0
    total_buy_amount = 0
    taker_fee = 0

    clear_screen()  # Clear the screen when starting the code
    load_account_details()  # Load account details when starting the code

    while True:
        choice = menu()
        if choice == '1':
            test_api_call()
        elif choice == '2':
            pair = input(f"Enter pair (default: {DEFAULT_PAIR}): ") or DEFAULT_PAIR
            print_current_pair_price_continuously(pair)
        elif choice == '3':
            add_fund()
        elif choice == '4':
            buy_pair_with_fund()
        elif choice == '5':
            show_trading_status()
        # elif choice == '6':
        #     start_trading_with_initial_fund()  # Disabled
        elif choice == '6':
            sell_pair_with_fund()
        elif choice == '7':
            show_profit()
        elif choice == '8':
            monitor_price()
        elif choice == '9':
            pair = input(f"Enter pair (default: {DEFAULT_PAIR}): ") or DEFAULT_PAIR
            get_fee_info(pair)
        elif choice == '10':
            reset_account()
        elif choice == '88':
            run_trading_bot()
        elif choice == '0':
            save_account_details()  # Save account details before exiting
            break
        else:
            print("Invalid choice. Please try again.")
        clear_screen()

def start_trading(initial_fund):
    global total_profit, total_loss, total_buy_amount, taker_fee  # Use global variables to track profit and loss
    fund = initial_fund
    bought_price = None

    # Execute the first buy immediately using the provided fund
    try:
        res = client.get_ticker("XBTMYR")
        last_trade_price = float(res['last_trade'])
        fee_info = client.get_fee_info("XBTMYR")
        taker_fee = float(fee_info['taker_fee'])
        buy_price = last_trade_price * 1.006
        trading_fee_value = buy_price * taker_fee
        if fund >= buy_price:
            bought_price = last_trade_price
            fund -= buy_price
            btc_bought = (buy_price * (1 - taker_fee)) / last_trade_price
            total_buy_amount += buy_price
            print(f"Initial Buy: Used {buy_price} MYR to buy {btc_bought} BTC at {bought_price} MYR, Remaining Fund: {fund} MYR, Taker Fee: {taker_fee * 100}% ({trading_fee_value} MYR)")
    except Exception as e:
        print(f"Error during initial buy: {e}")
        return

    while True:
        try:
            res = client.get_ticker("XBTMYR")
            last_trade_price = float(res['last_trade'])
            print(f"Last trade price: {last_trade_price} MYR")

            if bought_price is not None:
                # Calculate the sell price including the fee and profit margin
                target_sell_price = bought_price * 1.01
                sell_price = target_sell_price * 0.994
                cut_loss_price = bought_price * 0.98

                if last_trade_price >= sell_price:
                    fund += sell_price
                    profit = sell_price - bought_price
                    total_profit += profit
                    print(f"Sold XBT at {last_trade_price} MYR, Profit: {profit} MYR, Fund: {fund} MYR")
                    bought_price = None
                elif last_trade_price <= cut_loss_price:
                    fund += last_trade_price * 0.994
                    loss = bought_price - last_trade_price
                    total_loss += loss
                    print(f"Sold XBT at {last_trade_price} MYR to cut losses, Loss: {loss} MYR, Fund: {fund} MYR")
                    bought_price = None

            if bought_price is None:
                # Execute the next buy
                buy_price = last_trade_price * 1.006
                trading_fee_value = buy_price * taker_fee
                if fund >= buy_price:
                    bought_price = last_trade_price
                    fund -= buy_price
                    btc_bought = (buy_price * (1 - taker_fee)) / last_trade_price
                    total_buy_amount += buy_price
                    print(f"Bought {btc_bought} BTC at {bought_price} MYR, Used {buy_price} MYR, Remaining Fund: {fund} MYR, Taker Fee: {taker_fee * 100}% ({trading_fee_value} MYR)")

            print(f"Current Fund: {fund} MYR, Total Profit: {total_profit} MYR, Total Loss: {total_loss} MYR")
            if total_profit >= initial_fund * 0.10:
                print("Reached 10% profit margin. Stopping trading.")
                break
            if total_loss >= initial_fund * 0.05:
                print("Reached 5% loss margin. Stopping trading.")
                break

            print("Press 'q' to quit trading or any other key to continue...")
            if input().lower() == 'q':
                break

            time.sleep(5)  # Refresh every 5 seconds
        except Exception as e:
            print(f"Error during trading: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
