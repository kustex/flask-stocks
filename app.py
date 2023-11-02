from flask import Flask, render_template
import yfinance as yf
import plotly.express as px

app = Flask(__name__)

@app.route('/')
def index():
    # Fetch SPX data using yfinance
    spx_data = yf.download('^GSPC', start='2022-01-01', end='2023-01-01')

    # Create an interactive plot using Plotly
    fig = px.line(spx_data, x=spx_data.index, y='Close', title='S&P 500 (SPX) Stock Chart')
    graphJSON = fig.to_json()

    return render_template('index.html', graphJSON=graphJSON)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

