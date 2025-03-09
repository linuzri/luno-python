import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from luno_api_client import LunoAPIClient
import json
import os
import logging
from tqdm import tqdm
import matplotlib.pyplot as plt
from termcolor import colored

# Setup logging
logging.basicConfig(
    filename='backtest.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load configuration and initialize API
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)
    API_KEY = config.get('luno_api_key')
    API_SECRET = config.get('luno_api_secret')

if not API_KEY or not API_SECRET:
    raise ValueError("LUNO_API_KEY and LUNO_API_SECRET must be set in config.json")

client = LunoAPIClient(API_KEY, API_SECRET)

class HistoricalDataCollector:
    def __init__(self, client, pair="XBTMYR"):
        self.client = client
        self.pair = pair
        self.data = []
        
    def test_api_connection(self):
        """Test API connection before collecting data"""
        try:
            res = client.get_tickers()
            print(colored("API Connection Test: SUCCESS", "green"))
            return True
        except Exception as e:
            print(colored(f"API Connection Test FAILED: {e}", "red"))
            return False

    def collect_candle_data(self, days_back=30):
        """Collect historical candle data"""
        print(colored("\nCollecting historical data...", "cyan"))
        
        try:
            # Get recent trades instead of candles since Luno API has limited candle data
            since = int((datetime.now() - timedelta(days=days_back)).timestamp())
            trades = self.client.list_trades(self.pair, since=since)
            
            if not trades or 'trades' not in trades:
                print(colored("No trade data available", "red"))
                return None
                
            # Convert trades to OHLCV format
            df = pd.DataFrame(trades['trades'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['price'] = df['price'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # Resample to hourly candles
            hourly = df.set_index('timestamp').resample('1H').agg({
                'price': ['first', 'max', 'min', 'last'],
                'volume': 'sum'
            }).dropna()
            
            # Rename columns
            hourly.columns = ['open', 'high', 'low', 'close', 'volume']
            hourly = hourly.reset_index()
            
            # Save to CSV
            filename = f'historical_data_{self.pair}.csv'
            hourly.to_csv(filename, index=False)
            print(colored(f"Data saved to {filename}", "green"))
            print(f"Collected {len(hourly)} hourly candles")
            
            return hourly
            
        except Exception as e:
            print(colored(f"Error collecting data: {str(e)}", "red"))
            logging.error(f"Data collection error: {str(e)}")
            return None

    def collect_data_24h(self):
        """Collect last 24 hours of trade data"""
        try:
            since = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
            trades = self.client.list_trades(self.pair, since=since)
            
            if not trades or 'trades' not in trades:
                print(colored("No trade data available", "red"))
                return None
                
            # Convert trades to DataFrame
            df = pd.DataFrame(trades['trades'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['price'] = df['price'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # Resample to 5-minute candles
            candles = df.set_index('timestamp').resample('5T').agg({
                'price': ['first', 'max', 'min', 'last'],
                'volume': 'sum'
            }).dropna()
            
            candles.columns = ['open', 'high', 'low', 'close', 'volume']
            candles = candles.reset_index()
            
            return candles
            
        except Exception as e:
            print(colored(f"Error collecting 24h data: {str(e)}", "red"))
            return None

    def get_sample_data(self, days=30):
        """Generate sample data for testing"""
        print(colored("Generating sample data for testing...", "yellow"))
        
        # Generate dates with 5-minute intervals
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        dates = pd.date_range(start=start_time, end=end_time, freq='5min')
        
        # Generate sample price data with realistic patterns
        base_price = 100000  # Base BTC price in MYR
        price_series = pd.Series(index=dates)
        noise = np.random.normal(0, 1, len(dates))
        trend = np.linspace(0, 5000, len(dates))  # Add slight upward trend
        
        price_series = base_price + trend + noise * 500
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': price_series,
            'high': price_series * (1 + abs(noise) * 0.001),
            'low': price_series * (1 - abs(noise) * 0.001),
            'close': price_series + noise * 100,
            'volume': np.random.lognormal(0, 1, len(dates)) * 0.1
        })
        
        # Save both real and sample data
        filename = 'historical_data_XBTMYR.csv'
        df.to_csv(filename, index=False)
        print(colored(f"Sample data saved to {filename}", "green"))
        return df

class EnhancedBackTester:
    def __init__(self, data_file, initial_capital=1000):
        self.data = pd.read_csv(data_file)
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position = 0
        self.trades = []
        self.current_index = 0
        self.results = {'trades': [], 'metrics': {}}  # Add results dictionary
        
    def generate_parameter_combinations(self, parameter_ranges):
        """Generate all possible parameter combinations"""
        import itertools
        keys = parameter_ranges.keys()
        values = parameter_ranges.values()
        combinations = list(itertools.product(*values))
        return [dict(zip(keys, combo)) for combo in combinations]
        
    def calculate_equity_curve(self):
        """Calculate equity curve from trades"""
        equity = [self.initial_capital]
        current = self.initial_capital
        for trade in self.trades:
            current += trade['profit']
            equity.append(current)
        return equity

    def calculate_drawdown_series(self):
        """Calculate drawdown series"""
        equity_curve = self.calculate_equity_curve()
        peak = pd.Series(equity_curve).expanding(min_periods=1).max()
        drawdown = (pd.Series(equity_curve) - peak) / peak * 100
        return drawdown.values

    def run_backtest(self, strategy_params):
        """Run backtest with strategy parameters"""
        self.trades = []  # Reset trades
        self.current_capital = self.initial_capital
        self.position = 0
        
        for i in tqdm(range(50, len(self.data)), desc="Backtesting"):
            # Get historical window
            window = self.data.iloc[i-50:i]
            
            # Calculate indicators
            ma20 = window['close'].rolling(20).mean().iloc[-1]
            ma50 = window['close'].rolling(50).mean().iloc[-1]
            
            current_price = float(self.data.iloc[i]['close'])
            
            # Trading logic
            if self.position == 0:  # No position
                if ma20 > ma50:  # Buy signal
                    self.current_index = i
                    self.execute_buy(current_price)
            else:  # Have position
                entry_price = self.trades[-1]['entry_price']
                
                # Check exit conditions
                if (current_price <= entry_price * (1 - strategy_params['stop_loss']) or
                    current_price >= entry_price * (1 + strategy_params['take_profit'])):
                    self.execute_sell(current_price)
        
        # Calculate metrics after all trades
        metrics = self.calculate_metrics()
        return {'trades': self.trades, 'metrics': metrics}
    
    def execute_buy(self, price):
        """Execute buy order in backtest"""
        amount = self.current_capital * 0.95 / price  # Use 95% of capital
        self.position = amount
        self.trades.append({
            'entry_price': price,
            'amount': amount,
            'entry_time': self.data.iloc[self.current_index]['timestamp'],
            'profit': 0  # Initialize profit
        })
        
    def execute_sell(self, price):
        """Execute sell order in backtest"""
        if not self.trades:
            return
            
        last_trade = self.trades[-1]
        profit = (price - last_trade['entry_price']) * last_trade['amount']
        last_trade['exit_price'] = price
        last_trade['profit'] = profit
        self.current_capital += profit
        self.position = 0
    
    def calculate_metrics(self):
        """Calculate comprehensive trading metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'average_profit': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'max_drawdown': 0,
                'profit_factor': 0,
                'final_capital': self.initial_capital
            }
            
        profits = [t['profit'] for t in self.trades if 'profit' in t]
        winning_trades = [p for p in profits if p > 0]
        losing_trades = [p for p in profits if p < 0]  # Changed from <= to < to handle zero properly
        
        # Calculate total wins and losses safely
        total_wins = sum(winning_trades) if winning_trades else 0
        total_losses = abs(sum(losing_trades)) if losing_trades else 0
        
        # Calculate profit factor safely
        if total_losses > 0:
            profit_factor = total_wins / total_losses
        elif total_wins > 0:
            profit_factor = float('inf')
        else:
            profit_factor = 0
            
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trades) if self.trades else 0,
            'total_profit': sum(profits),
            'average_profit': sum(profits) / len(profits) if profits else 0,
            'largest_win': max(profits) if profits else 0,
            'largest_loss': min(profits) if profits else 0,
            'max_drawdown': self.calculate_max_drawdown(),
            'profit_factor': profit_factor,
            'final_capital': self.current_capital
        }

    def calculate_max_drawdown(self):
        """Calculate maximum drawdown"""
        capital = self.initial_capital
        peak = capital
        max_drawdown = 0
        
        for trade in self.trades:
            if 'profit' in trade:
                capital += trade['profit']
                peak = max(peak, capital)
                drawdown = (peak - capital) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown

    def calculate_risk_reward_ratio(self, trades):
        """Calculate risk/reward ratio"""
        if not trades:
            return 0
            
        avg_win = np.mean([t['profit'] for t in trades if t['profit'] > 0]) if any(t['profit'] > 0 for t in trades) else 0
        avg_loss = abs(np.mean([t['profit'] for t in trades if t['profit'] < 0])) if any(t['profit'] < 0 for t in trades) else 1
        return avg_win / avg_loss if avg_loss != 0 else float('inf')

    def optimize_strategy(self, parameter_ranges):
        """Optimize strategy parameters"""
        best_result = None
        best_metrics = None
        
        try:
            combinations = self.generate_parameter_combinations(parameter_ranges)
            for params in tqdm(combinations, desc="Optimizing Strategy"):
                results = self.run_backtest(params)
                metrics = results['metrics']
                
                # Initialize best metrics if None
                if best_metrics is None:
                    best_metrics = metrics
                    best_result = params
                    continue
                
                # Compare based on total profit and other factors
                if (metrics['total_profit'] > best_metrics['total_profit'] and 
                    metrics['max_drawdown'] <= best_metrics['max_drawdown'] * 1.5):  # Allow some drawdown flexibility
                    best_metrics = metrics
                    best_result = params
                    
        except Exception as e:
            logging.error(f"Error during optimization: {e}")
            return None, None
            
        return best_result, best_metrics

    def plot_results(self):
        """Plot backtest results"""
        if not self.results['trades']:
            print("No trades to plot")
            return
            
        plt.figure(figsize=(15, 10))
        
        # Plot equity curve
        equity_curve = self.calculate_equity_curve()
        plt.subplot(2, 1, 1)
        plt.plot(equity_curve)
        plt.title('Equity Curve')
        plt.grid(True)
        
        # Plot drawdown
        drawdown = self.calculate_drawdown_series()
        plt.subplot(2, 1, 2)
        plt.fill_between(range(len(drawdown)), drawdown, 0, color='red', alpha=0.3)
        plt.title('Drawdown')
        plt.grid(True)
        
        plt.tight_layout()
        plt.show()

def main():
    print(colored("Enhanced Backtester Starting...", "blue", attrs=["bold"]))
    
    # Initialize data collector with API client
    collector = HistoricalDataCollector(client)
    
    # Test API connection
    if not collector.test_api_connection():
        print(colored("Failed to connect to Luno API. Using sample data...", "yellow"))
        data = collector.get_sample_data()
    else:
        data = collector.collect_candle_data(days_back=30)
        if data is None:
            print(colored("Failed to collect real data. Using sample data...", "yellow"))
            data = collector.get_sample_data()
    
    if data is not None:
        try:
            # Initialize backtester
            tester = EnhancedBackTester('historical_data_XBTMYR.csv', initial_capital=1000)
            
            # Run initial backtest
            print("\nRunning initial backtest...")
            results = tester.run_backtest({
                'stop_loss': 0.02,
                'take_profit': 0.03,
                'ma_short': 20,
                'ma_long': 50
            })
            
            if results and 'metrics' in results:
                print("\nInitial Backtest Results:")
                for key, value in results['metrics'].items():
                    if isinstance(value, float):
                        print(f"{key.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        print(f"{key.replace('_', ' ').title()}: {value}")
                
                # Only proceed with optimization if initial backtest was successful
                print("\nOptimizing strategy parameters...")
                parameter_ranges = {
                    'ma_short': range(10, 31, 5),
                    'ma_long': range(40, 61, 5),
                    'stop_loss': [0.01, 0.02, 0.03],
                    'take_profit': [0.02, 0.03, 0.04]
                }
                
                best_params, best_metrics = tester.optimize_strategy(parameter_ranges)
                
                if best_params and best_metrics:
                    print("\nOptimal Strategy Parameters:")
                    for param, value in best_params.items():
                        print(f"{param}: {value}")
                    
                    print("\nOptimal Strategy Performance:")
                    for key, value in best_metrics.items():
                        if isinstance(value, float):
                            print(f"{key.replace('_', ' ').title()}: {value:.2f}")
                        else:
                            print(f"{key.replace('_', ' ').title()}: {value}")
            else:
                print("Initial backtest failed to produce results")
                
        except Exception as e:
            print(f"Error during backtesting: {e}")
            logging.error(f"Backtesting error: {e}")
    else:
        print("Failed to collect or generate data for backtesting")

if __name__ == '__main__':
    main()