import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import os
import sqlite3

from flask import Flask, render_template, request

app = Flask(__name__)
# Get the absolute path to the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(current_directory, 'stock_data.db')

# Function to calculate percentage returns
def calculate_returns(stock_data):
    # Calculate daily, weekly, monthly, and yearly returns
    stock_data = stock_data.set_index('Date')
    close_prices = stock_data['Close']
    daily_return = close_prices.pct_change(periods=1).iloc[-1] * 100

    # Weekly return (assuming 5 trading days in a week)
    weekly_return = close_prices.pct_change(periods=5).iloc[-1] * 100

    # Monthly return (assuming 20 trading days in a month)
    monthly_return = close_prices.pct_change(periods=20).iloc[-1] * 100

    # Yearly return (assuming 252 trading days in a year)
    yearly_return = close_prices.pct_change(periods=252).iloc[-1] * 100

    return round(daily_return, 2), round(weekly_return, 2), round(monthly_return, 2), round(yearly_return, 2)

def create_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock_data (
                        symbol TEXT,
                        date DATE,
                        open REAL,
                        high REAL,
                        low REAL,
                        close REAL,
                        volume INTEGER,
                        PRIMARY KEY (symbol, date)
                     )''')
    conn.commit()
    conn.close()

def fetch_stock_data(symbol, period='2y', interval='1d'):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stock_data WHERE symbol=? AND date >= date('now', '-2 year')", (symbol,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        # If data not found in the database, fetch from yfinance
        stock_data = yf.Ticker(symbol).history(period=period, interval=interval)
        stock_data = stock_data[['Open', 'High', 'Low', 'Close', 'Volume']]  # Select required columns
        stock_data.reset_index(inplace=True)

        # Store data in the database for future use
        conn = sqlite3.connect(DATABASE_PATH)
        stock_data.to_sql('stock_data', conn, if_exists='append', index=False)
        conn.close()
    else:
        # If data found in the database, convert it to DataFrame
        columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
        stock_data = pd.DataFrame(data, columns=columns)
    return stock_data

@app.route('/')
def index():
    create_database()
    symbols = ['TSLA', 'MSFT', 'GOOGL', 'NVDA', 'NFLX']
    interval = '1d'

    returns_data = {}
    for symbol in symbols:
        stock_data = fetch_stock_data(symbol)
        daily_return, weekly_return, monthly_return, yearly_return = calculate_returns(stock_data)
        returns_data[symbol] = {
            'daily_return': daily_return,
            'weekly_return': weekly_return,
            'monthly_return': monthly_return,
            'yearly_return': yearly_return
        }

    # Calculate correlation between stock returns
    returns_df = pd.DataFrame({symbol: fetch_stock_data(symbol)['Close'].pct_change() for symbol in symbols})
    correlation_table = returns_df.corr()

    return render_template('index.html', returns_data=returns_data, correlation_table=correlation_table)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

