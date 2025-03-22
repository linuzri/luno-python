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
    def __init__(self, config_path='config.json'):
        # Load strategy parameters from config
        with open(config_path, 'r') as f:
            config = json.load(f)
            trading_settings = config.get('trading_settings', {})
            self.stop_loss = trading_settings.get('stop_loss_percentage', 1.0) / 100
            self.take_profit = trading_settings.get('take_profit_percentage', 1.5) / 100
            self.max_position = trading_settings.get('max_position_percentage', 25.0) / 100
            self.trailing_stop = trading_settings.get('trailing_stop_percentage', 0.5) / 100
            
        self.highest_price = 0
        self.trailing_stop_price = 0
        
    def update_trailing_stop(self, current_price):
        """Update trailing stop price based on current price"""
        if current_price > self.highest_price:
            self.highest_price = current_price
            self.trailing_stop_price = current_price * (1 - self.trailing_stop)
        return self.trailing_stop_price

    def should_sell(self, entry_price, current_price):
        """Determine if position should be sold based on strategy"""
        # Update trailing stop
        trailing_stop_price = self.update_trailing_stop(current_price)
        
        # Check sell conditions
        take_profit_price = entry_price * (1 + self.take_profit)
        stop_loss_price = entry_price * (1 - self.stop_loss)
        
        if current_price >= take_profit_price:
            return True, "take_profit"
        elif current_price <= stop_loss_price:
            return True, "stop_loss"
        elif current_price <= trailing_stop_price:
            return True, "trailing_stop"
        return False, None

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

class TradeCalculator:
    def __init__(self):
        self.total_fees = 0
        self.total_volume = 0
    
    def calculate_fees(self, price, amount, is_maker=False):
        """Calculate trading fees based on order type"""
        try:
            fee_info = client.get_fee_info("XBTMYR")
            maker_fee = float(fee_info['maker_fee'])
            taker_fee = float(fee_info['taker_fee'])
            fee_rate = maker_fee if is_maker else taker_fee
            fee_amount = price * amount * fee_rate
            self.total_fees += fee_amount
            return fee_amount, fee_rate
        except Exception as e:
            logging.error(f"Error calculating fees: {e}")
            return 0, 0

class AdvancedTradingBot:
    def __init__(self):
        self.strategy = TradingStrategy()
        self.current_position = 0
        self.entry_price = 0
        self.total_profit = 0
        self.total_loss = 0  # Added this line
        self.total_trades = 0
        self.winning_trades = 0
        self.trade_history = []
        self.calculator = TradeCalculator()
        self.trades_summary = {
            'buys': {'volume': 0, 'fees': 0, 'total_cost': 0},
            'sells': {'volume': 0, 'fees': 0, 'total_revenue': 0}
        }
        self.price_history = []  # Add this line to initialize price history
        
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

    def log_trade(self, action, price, amount, fees=0, profit=0):
        trade = {
            'timestamp': datetime.now(),
            'action': action,
            'price': price,
            'amount': amount,
            'fees': fees,
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

    def execute_trade(self, action, price, amount, is_maker=False):
        try:
            fee_amount, fee_rate = self.calculator.calculate_fees(price, amount, is_maker)
            total_amount = price * amount

            if action == "BUY":
                actual_amount = amount * (1 - fee_rate)
                total_cost = total_amount + fee_amount
                
                # Update trade summary
                self.trades_summary['buys']['volume'] += actual_amount
                self.trades_summary['buys']['fees'] += fee_amount
                self.trades_summary['buys']['total_cost'] += total_cost
                
                print(colored(f"\nBUY Order Details:", "cyan"))
                print(f"Amount: {amount} BTC")
                print(f"Price: {price} MYR")
                print(f"Fee Rate: {fee_rate*100:.3f}%")
                print(f"Fee Amount: {fee_amount:.2f} MYR")
                print(f"Total Cost: {total_cost:.2f} MYR")
                print(f"Actual BTC Received: {actual_amount}")
                
                self.current_position = actual_amount
                self.entry_price = price
                
                # Reset trailing stop values for new position
                self.strategy.highest_price = price
                self.strategy.trailing_stop_price = price * (1 - self.strategy.trailing_stop)
                
            elif action == "SELL":
                actual_amount = amount * (1 - fee_rate)
                total_revenue = total_amount - fee_amount
                
                # Calculate real profit/loss including fees
                total_cost_basis = (amount / self.trades_summary['buys']['volume']) * self.trades_summary['buys']['total_cost']
                net_profit = total_revenue - total_cost_basis
                
                # Update trade summary
                self.trades_summary['sells']['volume'] += actual_amount
                self.trades_summary['sells']['fees'] += fee_amount
                self.trades_summary['sells']['total_revenue'] += total_revenue
                
                print(colored(f"\nSELL Order Details:", "cyan"))
                print(f"Amount: {amount} BTC")
                print(f"Price: {price} MYR")
                print(f"Fee Rate: {fee_rate*100:.3f}%")
                print(f"Fee Amount: {fee_amount:.2f} MYR")
                print(f"Total Revenue: {total_revenue:.2f} MYR")
                print(colored(f"Net Profit/Loss: {net_profit:.2f} MYR", "green" if net_profit > 0 else "red"))
                
                # Add reason for sell
                sell_reason = self.strategy.should_sell(self.entry_price, price)[1]
                print(colored(f"Sell reason: {sell_reason}", "yellow"))
                
                self.current_position = 0
                self.total_profit += net_profit if net_profit > 0 else 0
                self.total_loss += abs(net_profit) if net_profit < 0 else 0
                
            self.log_trade(action, price, amount, fee_amount, net_profit if action == "SELL" else 0)
            return True
            
        except Exception as e:
            logging.error(f"Error executing trade: {e}")
            return False

    def show_performance(self):
        """Enhanced performance display including fees and fund status"""
        print("\nFund Status:")
        print(colored(f"Initial Fund: {self.initial_fund:.2f} MYR", "cyan"))
        print(colored(f"Current Fund: {self.current_fund:.2f} MYR", "cyan"))
        print(colored(f"Available for Trading: {self.current_fund - self.min_trade_amount:.2f} MYR", "cyan"))
        print(colored(f"Minimum Trade Amount: {self.min_trade_amount:.2f} MYR", "cyan"))

        if self.current_fund > self.initial_fund:
            profit = self.current_fund - self.initial_fund
            print(colored(f"Total Return: +{profit:.2f} MYR (+{(profit/self.initial_fund)*100:.2f}%)", "green"))
        else:
            loss = self.initial_fund - self.current_fund
            print(colored(f"Total Return: -{loss:.2f} MYR (-{(loss/self.initial_fund)*100:.2f}%)", "red"))

        print("\nTrading Performance:")
        print(colored(f"Total Trading Volume: {self.calculator.total_volume:.8f} BTC", "cyan"))
        print(colored(f"Total Trading Fees: {self.calculator.total_fees:.2f} MYR", "yellow"))
        print(colored(f"Total Profit: {self.total_profit:.2f} MYR", "green"))
        print(colored(f"Total Loss: {self.total_loss:.2f} MYR", "red"))
        
        net_profit = self.total_profit - self.total_loss - self.calculator.total_fees
        print(colored(f"Net Profit (after fees): {net_profit:.2f} MYR", "green" if net_profit > 0 else "red"))
        
        if self.trade_history:
            print("\nRecent Trades (including fees):")
            headers = ["Time", "Action", "Price", "Amount", "Fees", "Net P/L"]
            recent_trades = self.trade_history[-5:]
            table = [[
                trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                trade['action'],
                f"{trade['price']:.2f}",
                f"{trade['amount']:.8f}",
                f"{trade['fees']:.2f}",
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

    def show_position_status(self, current_price):
        """Show current position status and indicators"""
        if self.current_position > 0:
            profit_loss = (current_price - self.entry_price) * self.current_position
            profit_loss_percent = ((current_price - self.entry_price) / self.entry_price) * 100
            
            # Calculate trailing stop level
            trailing_stop_price = self.strategy.trailing_stop_price
            
            print(colored("\nPosition Status:", "cyan"))
            print(f"Current Price: {current_price:.2f} MYR")
            print(f"Entry Price: {self.entry_price:.2f} MYR")
            print(f"Position Size: {self.current_position:.8f} BTC")
            print(f"Trailing Stop: {trailing_stop_price:.2f} MYR")
            
            if profit_loss >= 0:
                print(colored(f"Unrealized Profit: {profit_loss:.2f} MYR (+{profit_loss_percent:.2f}%)", "green"))
            else:
                print(colored(f"Unrealized Loss: {abs(profit_loss):.2f} MYR ({profit_loss_percent:.2f}%)", "red"))

    def run_trading_bot(self):
        try:
            logging.info("Starting trading bot...")
            while True:
                price = self.get_market_data()
                if not price:
                    continue

                # Add current price to price history
                self.price_history.append({
                    'timestamp': datetime.now(),
                    'price': price
                })

                # Maintain only last 50 prices
                if len(self.price_history) > 50:
                    self.price_history.pop(0)

                # Extract prices for analysis
                prices = [p['price'] for p in self.price_history]

                if self.current_position > 0:
                    should_sell, reason = self.strategy.should_sell(self.entry_price, price)
                    if should_sell:
                        self.execute_trade("SELL", price, self.current_position)
                        logging.info(f"Sell triggered by {reason} at price {price}")
                    else:
                        self.show_position_status(price)

                elif len(prices) >= 50 and self.analyze_market(prices):
                    amount = self.strategy.calculate_position_size(self.current_fund, price)
                    if amount > 0:
                        self.execute_trade("BUY", price, amount)
                        logging.info(f"Buy triggered at price {price}")

                time.sleep(10)

        except KeyboardInterrupt:
            logging.info("Trading bot stopped by user")
            print(colored("\nStopping trading bot...", "yellow"))
        except Exception as e:
            logging.error(f"Error in trading bot: {e}")
            print(colored(f"Error: {e}", "red"))

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
