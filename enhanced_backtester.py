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

# Replace the fixed DEFAULT_TIMESTAMP constant with a method
def get_default_timestamp():
    """Get timestamp from 1 hour ago"""
    current_time = datetime.now()
    one_hour_ago = current_time - timedelta(hours=1)  # Fixed syntax error
    return int(one_hour_ago.timestamp() * 1000)

# Add constant for strategy file
STRATEGY_FILE = 'optimal_strategy.json'

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle special values"""
    def default(self, obj):
        if isinstance(obj, float):
            if np.isinf(obj):
                return 999999
        return super().default(obj)

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

    def collect_recent_trades(self):
        """Collect trade data using dynamic timestamp"""
        try:
            print(colored("\nCollecting trade data...", "cyan"))
            timestamp = get_default_timestamp()
            print(f"Collecting data from {datetime.fromtimestamp(timestamp/1000)}")
            trades = self.client.list_trades(self.pair, since=timestamp)
            
            if not trades or 'trades' not in trades:
                print(colored("No trade data available", "red"))
                return None
                
            df = pd.DataFrame(trades['trades'])
            if len(df) == 0:
                print(colored("No trades found in the time period", "red"))
                return None
                
            # Convert and process data
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['price'] = df['price'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            print(f"Found {len(df)} trades")
            
            # Create OHLCV data with simplified resampling
            df_grouped = df.set_index('timestamp')
            ohlcv = pd.DataFrame({
                'open': df_grouped['price'].resample('1min').first(),
                'high': df_grouped['price'].resample('1min').max(),
                'low': df_grouped['price'].resample('1min').min(),
                'close': df_grouped['price'].resample('1min').last(),
                'volume': df_grouped['volume'].resample('1min').sum()
            }).dropna()
            
            ohlcv = ohlcv.reset_index()
            
            # Save data
            filename = 'historical_data_XBTMYR.csv'
            ohlcv.to_csv(filename, index=False)
            print(colored(f"Saved {len(ohlcv)} candles to {filename}", "green"))
            
            return ohlcv
            
        except Exception as e:
            print(colored(f"Error collecting trade data: {str(e)}", "red"))
            logging.error(f"Trade data collection error: {str(e)}")
            return None

    def get_sample_data(self, hours=24):
        """Generate sample data with realistic patterns"""
        print(colored("\nGenerating sample data...", "yellow"))
        
        # Generate 1-minute intervals for last 24 hours
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        dates = pd.date_range(start=start_time, end=end_time, freq='1min')
        
        # Get current price as base
        try:
            current_price = float(self.client.get_ticker(self.pair)['last_trade'])
        except:
            current_price = 100000  # Default base price if API fails
            
        # Generate more realistic price series with trends
        price = current_price
        prices = []
        trend = 0
        trend_duration = 0
        
        for _ in range(len(dates)):
            # Change trend randomly
            if trend_duration <= 0:
                trend = np.random.choice([-1, 0, 1], p=[0.3, 0.4, 0.3])  # Market trend bias
                trend_duration = np.random.randint(30, 120)  # Trend lasts 30-120 minutes
            
            # Generate price movement
            base_volatility = 0.001  # 0.1% base volatility
            trend_factor = trend * 0.0005  # Additional trend-based movement
            volatility = np.random.normal(trend_factor, base_volatility)
            
            # Add some random spikes
            if np.random.random() < 0.02:  # 2% chance of spike
                volatility *= np.random.choice([2, -2])
                
            price *= (1 + volatility)
            prices.append(price)
            trend_duration -= 1
        
        prices = np.array(prices)
        
        # Generate volume with some correlation to price changes
        volume_base = np.random.lognormal(0, 1, len(dates)) * 0.1
        price_changes = np.abs(np.diff(prices, prepend=prices[0])) / prices * 100
        volume = volume_base * (1 + price_changes)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * (1 + np.random.uniform(0, 0.002, len(dates))),
            'low': prices * (1 - np.random.uniform(0, 0.002, len(dates))),
            'close': prices * (1 + np.random.normal(0, 0.001, len(dates))),
            'volume': volume
        })
        
        # Ensure OHLC relationship is maintained
        df['high'] = df[['open', 'close', 'high']].max(axis=1)
        df['low'] = df[['open', 'close', 'low']].min(axis=1)
        
        # Add technical indicators
        df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()
        df['atr'] = self.calculate_atr(df)
        
        # Save enhanced sample data
        df.to_csv('historical_data_XBTMYR.csv', index=False)
        print(colored(f"Generated {len(df)} enhanced sample candles", "green"))
        return df

    def calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

class EnhancedBackTester:
    def __init__(self, data_file, initial_capital=1000):
        self.data = pd.read_csv(data_file)
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position = 0
        self.trades = []
        self.current_index = 0
        self.results = {'trades': [], 'metrics': {}}  # Add results dictionary
        self.load_optimal_strategy()
        self.output_file = 'backtest_results.txt'
        
    def load_optimal_strategy(self):
        """Load previously saved optimal strategy"""
        try:
            if os.path.exists(STRATEGY_FILE):
                with open(STRATEGY_FILE, 'r') as f:
                    self.optimal_strategy = json.load(f)
                print(colored("\nLoaded previous optimal strategy:", "cyan"))
                for param, value in self.optimal_strategy['parameters'].items():
                    print(f"{param}: {value}")
                print(f"Previous Performance: {self.optimal_strategy['metrics']['total_profit']:.2f} MYR")
            else:
                self.optimal_strategy = None
        except Exception as e:
            logging.error(f"Error loading optimal strategy: {e}")
            self.optimal_strategy = None

    def save_optimal_strategy(self, parameters, metrics):
        """Save current optimal strategy if better than previous"""
        try:
            current_strategy = {
                'parameters': parameters,
                'metrics': metrics,
                'timestamp': datetime.now().isoformat(),
                'initial_capital': self.initial_capital
            }

            if self.optimal_strategy is None:
                should_save = True
            else:
                # Compare with previous best
                prev_profit = self.optimal_strategy['metrics']['total_profit']
                curr_profit = metrics['total_profit']
                prev_drawdown = self.optimal_strategy['metrics']['max_drawdown']
                curr_drawdown = metrics['max_drawdown']
                
                should_save = (curr_profit > prev_profit and 
                             curr_drawdown <= prev_drawdown * 1.2)

            if should_save:
                with open(STRATEGY_FILE, 'w') as f:
                    json.dump(current_strategy, f, indent=4, cls=CustomJSONEncoder)
                self.optimal_strategy = current_strategy
                print(colored("\nNew optimal strategy saved!", "green"))
                print(f"Profit Improvement: {metrics['total_profit'] - (self.optimal_strategy.get('metrics', {}).get('total_profit', 0)):.2f} MYR")

        except Exception as e:
            logging.error(f"Error saving optimal strategy: {e}")

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
        self.trades = []
        self.current_capital = self.initial_capital
        self.position = 0
        
        # Convert timestamp to datetime if it's string
        if isinstance(self.data['timestamp'].iloc[0], str):
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        
        try:
            # Calculate additional indicators
            print("Calculating indicators...")
            self.data['vwap'] = (self.data['volume'] * self.data['close']).cumsum() / self.data['volume'].cumsum()
            self.data['atr'] = self.calculate_atr(self.data)
            self.data['volume_ma'] = self.data['volume'].rolling(window=20).mean()
            
            # Debug print
            print(f"Indicators calculated. Sample ATR: {self.data['atr'].head().tolist()}")
            
            # Rest of the method remains the same
            min_periods = max(strategy_params['ma_short'], strategy_params['ma_long'])
            
            for i in tqdm(range(min_periods, len(self.data)), desc="Backtesting"):
                window = self.data.iloc[i-min_periods:i]
                current_bar = self.data.iloc[i]
                
                # Calculate indicators
                ma_short = window['close'].rolling(strategy_params['ma_short']).mean().iloc[-1]
                ma_long = window['close'].rolling(strategy_params['ma_long']).mean().iloc[-1]
                vwap = current_bar['vwap']
                atr = current_bar['atr']
                volume_ratio = current_bar['volume'] / current_bar['volume_ma']
                
                if pd.isna(ma_short) or pd.isna(ma_long):
                    continue
                    
                current_price = float(current_bar['close'])
                
                # Enhanced trading logic
                if self.position == 0:  # No position
                    # Buy conditions:
                    # 1. Short MA crosses above Long MA
                    # 2. Price is near VWAP (within 0.5%)
                    # 3. Volume is above average
                    if (ma_short > ma_long and 
                        abs(current_price - vwap) / vwap < 0.005 and
                        volume_ratio > 1.2):
                        self.current_index = i
                        self.execute_buy(current_price)
                        print(f"BUY at {current_price} (Volume ratio: {volume_ratio:.2f})")
                else:  # Have position
                    entry_price = self.trades[-1]['entry_price']
                    price_change = (current_price - entry_price) / entry_price
                    
                    # Enhanced exit conditions:
                    # 1. Stop loss hit (adjusted by ATR)
                    # 2. Take profit hit
                    # 3. MA crossover in opposite direction
                    stop_loss = max(strategy_params['stop_loss'], 2 * atr / current_price)
                    if (price_change <= -stop_loss or
                        price_change >= strategy_params['take_profit'] or
                        (ma_short < ma_long and volume_ratio > 1)):
                        self.execute_sell(current_price)
                        print(f"SELL at {current_price} (Change: {price_change:.2%})")
            
            metrics = self.calculate_metrics()
            return {'trades': self.trades, 'metrics': metrics}
            
        except Exception as e:
            print(colored(f"Error in run_backtest: {str(e)}", "red"))
            logging.error(f"Backtest error: {str(e)}")
            return {'trades': [], 'metrics': self.calculate_metrics()}

    def calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

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
        """Optimize strategy parameters with persistence"""
        best_result = None
        best_metrics = None
        
        try:
            combinations = self.generate_parameter_combinations(parameter_ranges)
            
            # Start with previous optimal parameters if available
            if self.optimal_strategy:
                prev_params = self.optimal_strategy['parameters']
                if all(param in prev_params for param in parameter_ranges.keys()):
                    results = self.run_backtest(prev_params)
                    best_metrics = results['metrics']
                    best_result = prev_params
                    print(colored("\nTesting previous optimal strategy...", "cyan"))
                    print(f"Previous strategy profit: {best_metrics['total_profit']:.2f} MYR")

            # Test new combinations
            for params in tqdm(combinations, desc="Optimizing Strategy"):
                results = self.run_backtest(params)
                metrics = results['metrics']
                
                if best_metrics is None or metrics['total_profit'] > best_metrics['total_profit']:
                    best_metrics = metrics
                    best_result = params
            
            # Save if better than previous
            if best_result and best_metrics:
                self.save_optimal_strategy(best_result, best_metrics)
                
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

    def save_results_to_file(self, results, is_optimal=False):
        """Save backtest results to file"""
        try:
            with open(self.output_file, 'a') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Backtest Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*50}\n")
                
                if is_optimal:
                    f.write("OPTIMAL STRATEGY PARAMETERS:\n")
                else:
                    f.write("STRATEGY PARAMETERS:\n")
                    
                for param, value in results['parameters'].items():
                    f.write(f"{param}: {value}\n")
                
                f.write("\nPERFORMANCE METRICS:\n")
                for key, value in results['metrics'].items():
                    if isinstance(value, float):
                        f.write(f"{key.replace('_', ' ').title()}: {value:.2f}\n")
                    else:
                        f.write(f"{key.replace('_', ' ').title()}: {value}\n")
                
                f.write(f"{'='*50}\n")
                print(colored(f"\nResults saved to {self.output_file}", "green"))
        except Exception as e:
            logging.error(f"Error saving results to file: {e}")

def main():
    print(colored("Enhanced Backtester Starting...", "blue", attrs=["bold"]))
    
    collector = HistoricalDataCollector(client)
    
    # First try to get real data
    data = collector.collect_recent_trades()
    
    # Fall back to sample data if real data collection fails
    if data is None:
        print(colored("\nUsing sample data instead...", "yellow"))
        data = collector.get_sample_data()
    
    if data is not None:
        # Initialize backtester
        tester = EnhancedBackTester('historical_data_XBTMYR.csv', initial_capital=1000)
        
        # Run initial backtest with optimal strategy if available
        initial_params = (tester.optimal_strategy['parameters'] 
                        if tester.optimal_strategy 
                        else {
                            'stop_loss': 0.02,
                            'take_profit': 0.03,
                            'ma_short': 20,
                            'ma_long': 50
                        })
        
        print("\nRunning initial backtest...")
        results = tester.run_backtest(initial_params)
        
        # Show results and optimize
        if results and 'metrics' in results:
            # Save initial results
            initial_results = {
                'parameters': initial_params,
                'metrics': results['metrics']
            }
            tester.save_results_to_file(initial_results)
            
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
                # Save optimal results
                optimal_results = {
                    'parameters': best_params,
                    'metrics': best_metrics
                }
                tester.save_results_to_file(optimal_results, is_optimal=True)
                
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
            
    else:
        print("Failed to collect or generate data for backtesting")

if __name__ == '__main__':
    main()