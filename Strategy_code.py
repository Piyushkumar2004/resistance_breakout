import numpy as np
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import copy
import time

# Function to calculate True Range and Average True Range (ATR)
def ATR(DF, n):
    df = DF.copy()
    # Calculate High-Low, High-Previous Close, and Low-Previous Close differences
    df['H-L'] = abs(df['High'] - df['Low'])
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    
    # True Range is the maximum of the three ranges calculated above
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1, skipna=False)
    
    # Calculate the Average True Range (ATR) using a rolling mean
    df['ATR'] = df['TR'].rolling(n).mean()
    # Optionally, you could use Exponential Moving Average (EMA) for ATR calculation
    # df['ATR'] = df['TR'].ewm(span=n, adjust=False, min_periods=n).mean()
    
    df2 = df.drop(['H-L', 'H-PC', 'L-PC'], axis=1)
    return df2['ATR']

# Function to calculate the Cumulative Annual Growth Rate (CAGR) of a trading strategy
def CAGR(DF):
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()  # Calculate cumulative returns
    n = len(df) / (252 * 78)  # Assuming 252 trading days and 78 5-minute intervals in a day
    CAGR = (df["cum_return"].tolist()[-1]) ** (1 / n) - 1  # Calculate CAGR
    return CAGR

# Function to calculate annualized volatility of a trading strategy
def volatility(DF):
    df = DF.copy()
    vol = df["ret"].std() * np.sqrt(252 * 78)  # Annualized volatility
    return vol

# Function to calculate Sharpe Ratio; rf is the risk-free rate
def sharpe(DF, rf):
    df = DF.copy()
    sr = (CAGR(df) - rf) / volatility(df)  # Sharpe ratio calculation
    return sr

# Function to calculate maximum drawdown
def max_dd(DF):
    df = DF.copy()
    df["cum_return"] = (1 + df["ret"]).cumprod()  # Calculate cumulative returns
    df["cum_roll_max"] = df["cum_return"].cummax()  # Calculate cumulative rolling max
    df["drawdown"] = df["cum_roll_max"] - df["cum_return"]  # Drawdown calculation
    df["drawdown_pct"] = df["drawdown"] / df["cum_roll_max"]  # Drawdown percentage
    max_dd = df["drawdown_pct"].max()  # Maximum drawdown
    return max_dd

# Download historical intraday data (5-minute intervals) for selected stocks
tickers = ["MSFT", "AAPL", "FB", "AMZN", "INTC", "CSCO", "VZ", "IBM", "TSLA", "AMD"]

# Replace 'path_to_your_api_key' with the actual path to your Alpha Vantage API key file
key_path = "path_to_your_api_key"
ts = TimeSeries(key=open(key_path, 'r').read(), output_format='pandas')

ohlc_intraday = {}  # Dictionary to store OHLC data for each stock
api_call_count = 1  # Counter to track API calls (Alpha Vantage API limits to 5 calls per minute)
start_time = time.time()

# Loop through tickers to fetch OHLC data
for ticker in tickers:
    data, _ = ts.get_intraday(symbol=ticker, interval='5min', outputsize='full')  # Fetch data
    api_call_count += 1
    data.columns = ["Open", "High", "Low", "Close", "Volume"]  # Rename columns
    data = data.iloc[::-1]  # Reverse the data to have it in chronological order
    data = data.between_time('09:35', '16:00')  # Remove data outside regular trading hours
    ohlc_intraday[ticker] = data  # Store data in the dictionary
    
    # Ensure API rate limit is respected
    if api_call_count == 5:
        api_call_count = 1
        time.sleep(60 - ((time.time() - start_time) % 60.0))

tickers = ohlc_intraday.keys()  # Redefine tickers after removing any tickers with corrupted data

# Calculating ATR and rolling max price for each stock, and consolidating this info by stock in a separate dataframe
ohlc_dict = copy.deepcopy(ohlc_intraday)
tickers_signal = {}  # Dictionary to store trading signals for each stock
tickers_ret = {}  # Dictionary to store returns for each stock

# Loop through each ticker to calculate ATR, rolling max/min prices, and volume
for ticker in tickers:
    print("Calculating ATR and rolling max price for", ticker)
    ohlc_dict[ticker]["ATR"] = ATR(ohlc_dict[ticker], 20)  # Calculate ATR with a period of 20
    ohlc_dict[ticker]["roll_max_cp"] = ohlc_dict[ticker]["High"].rolling(20).max()  # Rolling max of High prices
    ohlc_dict[ticker]["roll_min_cp"] = ohlc_dict[ticker]["Low"].rolling(20).min()  # Rolling min of Low prices
    ohlc_dict[ticker]["roll_max_vol"] = ohlc_dict[ticker]["Volume"].rolling(20).max()  # Rolling max of Volume
    ohlc_dict[ticker].dropna(inplace=True)  # Drop rows with NaN values
    tickers_signal[ticker] = ""  # Initialize signal as empty
    tickers_ret[ticker] = [0]  # Initialize return as 0

# Identifying signals and calculating intraday returns (factoring in stop loss)
for ticker in tickers:
    print("Calculating returns for", ticker)
    for i in range(1, len(ohlc_dict[ticker])):
        if tickers_signal[ticker] == "":
            tickers_ret[ticker].append(0)  # No position, no return
            
            # Buy signal: price breaks rolling max and volume spikes
            if (ohlc_dict[ticker]["High"][i] >= ohlc_dict[ticker]["roll_max_cp"][i] and 
                ohlc_dict[ticker]["Volume"][i] > 1.5 * ohlc_dict[ticker]["roll_max_vol"][i - 1]):
                tickers_signal[ticker] = "Buy"
            
            # Sell signal: price breaks rolling min and volume spikes
            elif (ohlc_dict[ticker]["Low"][i] <= ohlc_dict[ticker]["roll_min_cp"][i] and 
                  ohlc_dict[ticker]["Volume"][i] > 1.5 * ohlc_dict[ticker]["roll_max_vol"][i - 1]):
                tickers_signal[ticker] = "Sell"
        
        # If Buy signal is active
        elif tickers_signal[ticker] == "Buy":
            # Stop loss hit: sell position
            if ohlc_dict[ticker]["Low"][i] < ohlc_dict[ticker]["Close"][i - 1] - ohlc_dict[ticker]["ATR"][i - 1]:
                tickers_signal[ticker] = ""
                tickers_ret[ticker].append(((ohlc_dict[ticker]["Close"][i - 1] - ohlc_dict[ticker]["ATR"][i - 1]) / ohlc_dict[ticker]["Close"][i - 1]) - 1)
            
            # Reverse to Sell signal
            elif (ohlc_dict[ticker]["Low"][i] <= ohlc_dict[ticker]["roll_min_cp"][i] and 
                  ohlc_dict[ticker]["Volume"][i] > 1.5 * ohlc_dict[ticker]["roll_max_vol"][i - 1]):
                tickers_signal[ticker] = "Sell"
                tickers_ret[ticker].append((ohlc_dict[ticker]["Close"][i] / ohlc_dict[ticker]["Close"][i - 1]) - 1)
            else:
                tickers_ret[ticker].append((ohlc_dict[ticker]["Close"][i] / ohlc_dict[ticker]["Close"][i - 1]) - 1)
        
        # If Sell signal is active
        elif tickers_signal[ticker] == "Sell":
            # Stop loss hit: cover position
            if ohlc_dict[ticker]["High"][i] > ohlc_dict[ticker]["Close"][i - 1] + ohlc_dict[ticker]["ATR"][i - 1]:
                tickers_signal[ticker] = ""
                tickers_ret[ticker].append((ohlc_dict[ticker]["Close"][i - 1] / (ohlc_dict[ticker]["Close"][i - 1] + ohlc_dict[ticker]["ATR"][i - 1])) - 1)
            
            # Reverse to Buy signal
            elif (ohlc_dict[ticker]["High"][i] >= ohlc_dict[ticker]["roll_max_cp"][i] and 
                  ohlc_dict[ticker]["Volume"][i] > 1.5 * ohlc_dict[ticker]["roll_max_vol"][i - 1]):
                tickers_signal[ticker] = "Buy"
                tickers_ret[ticker].append((ohlc_dict[ticker]["Close"][i - 1] / ohlc_dict[ticker]["Close"][i]) - 1)
            else:
                tickers_ret[ticker].append((ohlc_dict[ticker]["Close"][i - 1] / ohlc_dict[ticker]["Close"][i]) - 1)
    
    # Add calculated returns to the dataframe
    ohlc_dict[ticker]["ret"] = np.array(tickers_ret[ticker])

# Calculating overall strategy's KPIs
strategy_df = pd.DataFrame()
for ticker in tickers:
    strategy_df[ticker] = ohlc_dict[ticker]["ret"]  # Aggregate returns for each stock
strategy_df["ret"] = strategy_df.mean(axis=1)  # Average return of the strategy

# Display the KPIs
print("CAGR:", CAGR(strategy_df))
print("Sharpe Ratio:", sharpe(strategy_df, 0.025))
print("Max Drawdown:", max_dd(strategy_df))

# Visualization of strategy return
(1 + strategy_df["ret"]).cumprod().plot()

# Calculating individual stock's KPIs
cagr = {}
sharpe_ratios = {}
max_drawdown = {}
for ticker in tickers:
    print("Calculating KPIs for", ticker)
    cagr[ticker] = CAGR(ohlc_dict[ticker])  # CAGR for each stock
    sharpe_ratios[ticker] = sharpe(ohlc_dict[ticker], 0.025)  # Sharpe Ratio for each stock
    max_drawdown[ticker] = max_dd(ohlc_dict[ticker])  # Max Drawdown for each stock

# Create a DataFrame to display individual stock KPIs
KPI_df = pd.DataFrame([cagr, sharpe_ratios, max_drawdown], index=["Return", "Sharpe Ratio", "Max Drawdown"])      
print(KPI_df.T)
