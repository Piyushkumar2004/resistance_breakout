# Intraday Trading Strategy Script

This repository contains a Python script implementing an intraday trading strategy based on the Average True Range (ATR) and volume breakout signals. The strategy is designed to be applied to historical 5-minute interval data for selected stocks.

## Key Features

- **ATR Calculation**: The script calculates the True Range (TR) and Average True Range (ATR) for each stock. ATR is used to set stop-loss levels for trades.
- **Signal Generation**: The strategy generates buy and sell signals based on the breakout of rolling maximum and minimum prices, with a significant increase in volume.
- **Risk Management**: Stop-loss levels are set using the ATR to manage risk on each trade.
- **Performance Metrics**: The script calculates key performance indicators (KPIs) such as CAGR, Sharpe Ratio, and Maximum Drawdown for both individual stocks and the overall strategy.

## Files in the Repository

- **trading_strategy.py**: The main script containing the trading strategy logic.
- **requirements.txt**: A list of Python packages required to run the script.

## How It Works

1. **Data Download**: Historical intraday data (5-minute intervals) is downloaded for selected stocks using the Alpha Vantage API.
2. **ATR and Signal Calculation**: The script calculates the ATR and identifies buy/sell signals based on price and volume breakouts.
3. **Backtesting**: The strategy is backtested over the historical data to calculate returns and evaluate performance.
4. **KPI Calculation**: Key performance indicators like CAGR, Sharpe Ratio, and Maximum Drawdown are calculated for each stock and the overall strategy.

## Installation and Usage

1. **Clone the repository**:
    ```bash
    git clone https://github.com/your_username/your_repository_name.git
    cd your_repository_name
    ```

2. **Install the required Python packages**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up Alpha Vantage API**:
   - Obtain an API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).
   - Save the API key in a text file at the specified `key_path`.

4. **Run the script**:
    ```bash
    python trading_strategy.py
    ```

## Performance Metrics

- **CAGR**: Compound Annual Growth Rate measures the mean annual growth rate of the strategy.
- **Sharpe Ratio**: Measures the risk-adjusted return of the strategy.
- **Maximum Drawdown**: Represents the maximum observed loss from a peak to a trough.

## Example Output

```python
CAGR: 0.20
Sharpe Ratio: 1.50
Max Drawdown: 0.15
