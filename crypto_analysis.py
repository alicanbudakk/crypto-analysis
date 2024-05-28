import pandas as pd
import numpy as np
import time
import pytz
import logging
from tradingview_ta import TA_Handler, Interval, Exchange

# Setup logging
logging.basicConfig(filename='crypto_analysis.log', level=logging.INFO, format='%(asctime)s %(message)s')

# List of assets to analyze
assets = [
    {"symbol": "APTUSDT.P", "exchange": "BINANCE"},
    {"symbol": "OPUSDT.P", "exchange": "BINANCE"},
    {"symbol": "ADAUSDT.P", "exchange": "BINANCE"},
    {"symbol": "AVAXUSDT.P", "exchange": "BINANCE"},
    {"symbol": "SOLUSDT.P", "exchange": "BINANCE"},
    {"symbol": "APEUSDT.P", "exchange": "BINANCE"},
    {"symbol": "DOTUSDT.P", "exchange": "BINANCE"},
    {"symbol": "EOSUSDT.P", "exchange": "BINANCE"},
    {"symbol": "FILUSDT.P", "exchange": "BINANCE"},
    {"symbol": "FTMUSDT.P", "exchange": "BINANCE"},
    {"symbol": "GALAUSDT.P", "exchange": "BINANCE"},
    {"symbol": "GMTUSDT.P", "exchange": "BINANCE"},
    {"symbol": "ICXUSDT.P", "exchange": "BINANCE"},
    {"symbol": "IMXUSDT.P", "exchange": "BINANCE"},
    {"symbol": "LRCUSDT.P", "exchange": "BINANCE"},
    {"symbol": "MANAUSDT.P", "exchange": "BINANCE"},
    {"symbol": "MKRUSDT.P", "exchange": "BINANCE"},
    {"symbol": "RUNEUSDT.P", "exchange": "BINANCE"},
    {"symbol": "SANDUSDT.P", "exchange": "BINANCE"},
    {"symbol": "XRPUSDT.P", "exchange": "BINANCE"},
    {"symbol": "DOGEUSDT.P", "exchange": "BINANCE"},
    {"symbol": "ZECUSDT.P", "exchange": "BINANCE"},
]

# Scoring system
score_map = {
    'Buy': 1,
    'Strong Buy': 1,
    'Sell': -1,
    'Strong Sell': -1,
    'Neutral': 0
}

# Fetch live cryptocurrency data from TradingView
def fetch_live_data(symbol, exchange, interval=Interval.INTERVAL_1_HOUR):
    try:
        handler = TA_handler(
            symbol=symbol,
            screener="crypto",
            exchange=exchange,
            interval=interval
        )
        analysis = handler.get_analysis()
        
        # Convert the timestamp to CDT
        timestamp_utc = pd.to_datetime('now', utc=True)
        timestamp_cdt = timestamp_utc.tz_convert('America/Chicago').strftime('%H:%M')
        
        return {
            'timestamp': timestamp_cdt,
            'Recommendation': analysis.summary['RECOMMENDATION'],
            'MA50': analysis.indicators.get("SMA50", np.nan),
            'MA200': analysis.indicators.get("SMA200", np.nan),
            'RSI': analysis.indicators["RSI"],
            'MACD': analysis.indicators["MACD.macd"],
            'MACD_Signal': analysis.indicators["MACD.signal"],
            'Close': analysis.indicators["close"],  # Include close price for pattern detection
            'Pattern': 'None',  # Placeholder for pattern detection
            'Signal': 'Neutral'
        }
    except Exception as e:
        logging.error(f"Error fetching live data for {symbol}: {e}")
        return None

# Detect chart patterns
def detect_patterns(data):
    for symbol, details in data.items():
        if details is None:
            continue

        try:
            ma50 = details['MA50']
            ma200 = details['MA200']
            rsi = details['RSI']
            macd = details['MACD']
            macd_signal = details['MACD_Signal']
            close_price = details['Close']
            
            # Golden Cross and Death Cross
            if ma50 > ma200:
                details['Pattern'] = 'Golden Cross'
                details['Signal'] = 'Buy'
            elif ma50 < ma200:
                details['Pattern'] = 'Death Cross'
                details['Signal'] = 'Sell'
            
            # RSI Overbought and Oversold
            if rsi > 70:
                details['RSI_Signal'] = 'Sell'
            elif rsi < 30:
                details['RSI_Signal'] = 'Buy'
            else:
                details['RSI_Signal'] = 'Neutral'

            # MACD Cross
            if macd > macd_signal:
                details['MACD_Signal'] = 'Buy'
            elif macd < macd_signal:
                details['MACD_Signal'] = 'Sell'
            else:
                details['MACD_Signal'] = 'Neutral'

            # Simplified detection for complex patterns
            closes = np.array([details['Close']])  # Assuming previous close prices are fetched and stored
            if len(closes) >= 5:
                # Head and Shoulders (simplified detection)
                if closes[-5] < closes[-4] > closes[-3] < closes[-2] > closes[-1]:
                    details['Pattern'] = 'Head and Shoulders'
                    details['Complex_Signal'] = 'Sell'

                # Cup and Handle (simplified detection)
                elif closes[-5] < closes[-4] < closes[-3] > closes[-2] > closes[-1]:
                    details['Pattern'] = 'Cup and Handle'
                    details['Complex_Signal'] = 'Buy'

                # Triangle (simplified detection)
                elif closes[-5] > closes[-4] < closes[-3] > closes[-2] < closes[-1]:
                    details['Pattern'] = 'Triangle'
                    details['Complex_Signal'] = 'Neutral'

                # Flag (simplified detection)
                elif closes[-5] > closes[-4] > closes[-3] > closes[-2] > closes[-1]:
                    details['Pattern'] = 'Flag'
                    details['Complex_Signal'] = 'Sell'
                elif closes[-5] < closes[-4] < closes[-3] < closes[-2] < closes[-1]:
                    details['Pattern'] = 'Flag'
                    details['Complex_Signal'] = 'Buy'

                # Wedge (simplified detection)
                elif closes[-5] > closes[-4] > closes[-3] > closes[-2] < closes[-1]:
                    details['Pattern'] = 'Wedge'
                    details['Complex_Signal'] = 'Buy'
                elif closes[-5] < closes[-4] < closes[-3] < closes[-2] > closes[-1]:
                    details['Pattern'] = 'Wedge'
                    details['Complex_Signal'] = 'Sell'

            if 'Complex_Signal' not in details:
                details['Complex_Signal'] = 'Neutral'
        except Exception as e:
            logging.error(f"Error detecting patterns for {symbol}: {e}")
    
    return data

# Calculate overall signal
def calculate_overall_signal(data):
    for symbol, details in data.items():
        if details is None:
            continue

        try:
            score = 0
            # Aggregate signals from different indicators and patterns
            signals = [
                details.get('Signal', 'Neutral'),
                details.get('RSI_Signal', 'Neutral'),
                details.get('MACD_Signal', 'Neutral'),
                details.get('Complex_Signal', 'Neutral'),
                details['Recommendation']
            ]
            
            for signal in signals:
                score += score_map.get(signal, 0)
            
            # Determine the overall signal
            if score > 0:
                details['Overall'] = 'Long'
            else:
                details['Overall'] = 'Short'
        except Exception as e:
            logging.error(f"Error calculating overall signal for {symbol}: {e}")

    return data

# Display live data in a detailed table format with color formatting
def display_live_data(data):
    try:
        table_data = []
        for symbol, details in data.items():
            if details is None:
                continue

            close_price = details['Close']
            leverage = 5
            initial_investment = 100
            stop_loss = close_price * (1 - (0.15 / leverage))
            stop_profit = close_price * (1 + (0.15 / leverage))
            row = {
                'Coin Name': symbol,
                'Time': details['timestamp'],
                'Current Price': close_price,
                'Overall Signal': details['Overall'],
                'Stop Loss': stop_loss,
                'Stop Profit': stop_profit
            }
            table_data.append(row)
        
        df = pd.DataFrame(table_data)
        
        def color_coin_name(val):
            color = 'green' if val['Overall Signal'] == 'Long' else 'red'
            return [f'color: {color}']*len(val)
        
        styled_df = df.style.apply(color_coin_name, axis=1)
        
        # Log the output to a file
        logging.info(styled_df.render())
    except Exception as e:
        logging.error(f"Error displaying live data: {e}")

# Main program for live data
if __name__ == "__main__":
    try:
        interval = Interval.INTERVAL_1_HOUR  # Set interval to 1 hour

        data = {}
        for asset in assets:
            symbol = asset["symbol"]
            exchange = asset["exchange"]
            data[symbol] = fetch_live_data(symbol, exchange, interval)
        
        # Detect patterns and generate signals
        data = detect_patterns(data)
        
        # Calculate overall signal
        data = calculate_overall_signal(data)
        
        # Display live data
        display_live_data(data)
    except Exception as e:
        logging.error(f"Error in main program: {e}")
