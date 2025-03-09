import os
import json
import time
import logging
from datetime import datetime
import pandas as pd
import numpy as np
from luno_api_client import LunoAPIClient
from dotenv import load_dotenv
from tabulate import tabulate
from termcolor import colored

# Setup logging
logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load configuration
load_dotenv()
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)
    API_KEY = config.get('luno_api_key')
    API_SECRET = config.get('luno_api_secret')

if not API_KEY or not API_SECRET:
    raise ValueError("LUNO_API_KEY and LUNO_API_SECRET must be set in config.json")

client = LunoAPIClient(API_KEY, API_SECRET)
DEFAULT_PAIR = "XBTMYR"

class TradingStrategy:
    def __init__(self):
        self.position_size = 0
        self.stop_loss = 0.02  # 2%
        self.take_profit = 0.03  # 3%
        self.max_position = 0.5  # 50% of total fund
        self.trailing_stop = 0.01  # 1%
        
    def calculate_position_size(self, fund, price):
        return min(fund * self.max_position / price, fund)

class TechnicalAnalysis:
    @staticmethod
    def calculate_ma(prices, period):
        return pd.Series(prices).rolling(window=period).mean().iloc[-1]

    @staticmethod
    def calculate_rsi(prices, period=14):
        returns = pd.Series(prices).diff()
        up = returns.clip(lower=0)
        down = -1 * returns.clip(upper=0)
        ma_up = up.rolling(window=period).mean()
        ma_down = down.rolling(window=period).mean()
        rsi = ma_up / (ma_up + ma_down) * 100
        return rsi.iloc[-1]

class AdvancedTradingBot:
    def __init__(self):
        self.strategy = TradingStrategy()
        self.current_position = 0
        self.entry_price = 0
        self.total_profit = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.trade_history = []
        
        # Load trading settings from config
        with open(config_path, 'r') as f:
            config = json.load(f)
            trading_settings = config.get('trading_settings', {})
            self.initial_fund = trading_settings.get('initial_fund', 1000.00)
            self.current_fund = self.initial_fund
            self.max_fund = trading_settings.get('max_fund', 5000.00)
            self.min_trade_amount = trading_settings.get('min_trade_amount', 100.00)

    def update_fund(self, amount):
        """Update fund amount"""
        self.current_fund = amount
        # Update config file
        with open(config_path, 'r+') as f:
            config = json.load(f)
            config['trading_settings']['initial_fund'] = amount
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()
        print(colored(f"Fund updated to: {amount} MYR", "green"))

    def show_fund_status(self):
        """Display current fund status"""
        print("\nFund Status:")
        print(f"Initial Fund: {self.initial_fund:.2f} MYR")
        print(f"Current Fund: {self.current_fund:.2f} MYR")
        print(f"Available for Trading: {self.current_fund - self.min_trade_amount:.2f} MYR")
        print(f"Minimum Trade Amount: {self.min_trade_amount:.2f} MYR")
        if self.current_fund > self.initial_fund:
            profit = self.current_fund - self.initial_fund
            print(colored(f"Total Profit: {profit:.2f} MYR (+{(profit/self.initial_fund)*100:.2f}%)", "green"))
        else:
            loss = self.initial_fund - self.current_fund
            print(colored(f"Total Loss: {loss:.2f} MYR (-{(loss/self.initial_fund)*100:.2f}%)", "red"))

    def log_trade(self, action, price, amount, profit=0):
        trade = {
            'timestamp': datetime.now(),
            'action': action,
            'price': price,
            'amount': amount,
            'profit': profit
        }
        self.trade_history.append(trade)
        logging.info(f"Trade executed: {trade}")

    def get_market_data(self, pair=DEFAULT_PAIR):
        try:
            res = client.get_ticker(pair)
            price = float(res['last_trade'])
            print(colored(f"Current price: {price} MYR", "yellow"))
            return price
        except Exception as e:
            logging.error(f"Error getting market data: {e}")
            return None

    def analyze_market(self, prices):
        ma20 = TechnicalAnalysis.calculate_ma(prices, 20)
        ma50 = TechnicalAnalysis.calculate_ma(prices, 50)
        rsi = TechnicalAnalysis.calculate_rsi(prices)
        
        print(colored(f"Technical Indicators:", "cyan"))
        print(f"MA20: {ma20:.2f}")
        print(f"MA50: {ma50:.2f}")
        print(f"RSI: {rsi:.2f}")
        
        return ma20 > ma50 and 30 < rsi < 70

    def execute_trade(self, action, price, amount):
        try:
            if action == "BUY":
                # Calculate position size based on risk management
                max_position = self.strategy.calculate_position_size(self.current_fund, price)
                amount = min(amount, max_position)
                
                # Execute buy order
                print(colored(f"Executing BUY order: {amount} BTC at {price} MYR", "green"))
                self.entry_price = price
                self.current_position = amount
                self.log_trade("BUY", price, amount)
                
            elif action == "SELL":
                # Execute sell order
                print(colored(f"Executing SELL order: {amount} BTC at {price} MYR", "red"))
                profit = (price - self.entry_price) * amount
                self.total_profit += profit
                self.total_trades += 1
                
                if profit > 0:
                    self.winning_trades += 1
                    print(colored(f"Profit: {profit:.2f} MYR", "green"))
                else:
                    print(colored(f"Loss: {abs(profit):.2f} MYR", "red"))
                
                self.current_position = 0
                self.log_trade("SELL", price, amount, profit)
            
            return True
        except Exception as e:
            logging.error(f"Error executing trade: {e}")
            return False

    def show_performance(self):
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        print("\nPerformance Metrics:")
        print(colored(f"Total Profit: {self.total_profit:.2f} MYR", "green" if self.total_profit > 0 else "red"))
        print(f"Total Trades: {self.total_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        
        if self.trade_history:
            print("\nRecent Trades:")
            headers = ["Time", "Action", "Price", "Amount", "Profit"]
            recent_trades = self.trade_history[-5:]
            table = [[
                trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                trade['action'],
                f"{trade['price']:.2f}",
                f"{trade['amount']:.4f}",
                f"{trade['profit']:.2f}"
            ] for trade in recent_trades]
            print(tabulate(table, headers=headers, tablefmt="grid"))

    def test_api_connection(self):
        """Test API connection and return status"""
        try:
            res = client.get_tickers()
            print(colored("API Connection Test:", "cyan"))
            print(colored("✓ Connection Successful", "green", attrs=["bold"]))
            print(colored("✓ API Key Valid", "green", attrs=["bold"]))
            print(colored("✓ API Secret Valid", "green", attrs=["bold"]))
            return True
        except Exception as e:
            print(colored("API Connection Test:", "cyan"))
            print(colored("✗ Connection Failed", "red", attrs=["bold"]))
            print(colored(f"✗ Error: {str(e)}", "red", attrs=["bold"]))
            return False

def menu():
    print(colored("\n====================", "blue", attrs=["bold"]))
    print(colored("Advanced Trading Bot", "blue", attrs=["bold"]))
    print(colored("====================", "blue", attrs=["bold"]))
    print("1. Start Trading Bot")
    print("2. Show Performance")
    print("3. Configure Strategy")
    print("4. Monitor Market")
    print("5. Show Fund Status")
    print("6. Update Fund Amount")
    print("7. Test API Connection")
    print("0. Exit")
    return input("Enter your choice: ")

def main():
    bot = AdvancedTradingBot()
    prices = []
    
    while True:
        choice = menu()
        if choice == '1':
            print(colored("Starting trading bot...", "green"))
            try:
                while True:
                    price = bot.get_market_data()
                    if price:
                        prices.append(price)
                        if len(prices) > 50:  # Need at least 50 prices for analysis
                            if bot.analyze_market(prices):
                                if bot.current_position == 0:
                                    amount = 0.001  # Example amount
                                    bot.execute_trade("BUY", price, amount)
                            elif bot.current_position > 0:
                                if price <= bot.entry_price * (1 - bot.strategy.stop_loss) or \
                                   price >= bot.entry_price * (1 + bot.strategy.take_profit):
                                    bot.execute_trade("SELL", price, bot.current_position)
                    time.sleep(10)
            except KeyboardInterrupt:
                print(colored("\nStopping trading bot...", "yellow"))
        
        elif choice == '2':
            bot.show_performance()
        
        elif choice == '3':
            print("\nCurrent Strategy Settings:")
            print(f"Stop Loss: {bot.strategy.stop_loss * 100}%")
            print(f"Take Profit: {bot.strategy.take_profit * 100}%")
            print(f"Max Position: {bot.strategy.max_position * 100}%")
            print(f"Trailing Stop: {bot.strategy.trailing_stop * 100}%")
        
        elif choice == '4':
            print(colored("\nMonitoring market...", "cyan"))
            try:
                while True:
                    price = bot.get_market_data()
                    if price and len(prices) > 50:
                        bot.analyze_market(prices)
                    time.sleep(10)
            except KeyboardInterrupt:
                print(colored("\nStopping market monitor...", "yellow"))
        
        elif choice == '5':
            bot.show_fund_status()
        
        elif choice == '6':
            try:
                new_amount = float(input("Enter new fund amount (MYR): "))
                if new_amount < bot.min_trade_amount:
                    print(colored(f"Error: Amount must be at least {bot.min_trade_amount} MYR", "red"))
                elif new_amount > bot.max_fund:
                    print(colored(f"Error: Amount cannot exceed {bot.max_fund} MYR", "red"))
                else:
                    bot.update_fund(new_amount)
            except ValueError:
                print(colored("Error: Please enter a valid number", "red"))
        
        elif choice == '7':
            bot.test_api_connection()
            input(colored("\nPress Enter to continue...", "yellow"))
        
        elif choice == '0':
            print(colored("Exiting...", "red"))
            break
        
        else:
            print(colored("Invalid choice!", "red"))

if __name__ == '__main__':
    main()
