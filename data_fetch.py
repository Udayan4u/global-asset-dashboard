import yfinance as yf
import pandas as pd
import datetime

ASSET_CLASSES = {
    'Equity': ['SPY', 'QQQ', 'VEU'],
    'Fixed Income': ['TLT', 'BND', 'AGG'],
    'Commodities': ['GLD', 'USO', 'DBC'],
    'Bitcoin': ['BTC-USD', 'IBIT'],
    'FX': ['EURUSD=X', 'USDJPY=X']
}

TICKER_NAMES = {
    'SPY': 'SPDR S&P 500 ETF Trust',
    'QQQ': 'Invesco QQQ Trust',
    'VEU': 'Vanguard FTSE All-World ex-US ETF',
    'TLT': 'iShares 20+ Year Treasury Bond ETF',
    'BND': 'Vanguard Total Bond Market ETF',
    'AGG': 'iShares Core U.S. Aggregate Bond ETF',
    'GLD': 'SPDR Gold Shares',
    'USO': 'United States Oil Fund LP',
    'DBC': 'Invesco DB Commodity Index Tracking Fund',
    'BTC-USD': 'Bitcoin USD',
    'IBIT': 'iShares Bitcoin Trust ETF',
    'EURUSD=X': 'EUR/USD',
    'USDJPY=X': 'USD/JPY'
}

def get_prices(start_date='2024-01-01'):
    data = {}
    for cls, tickers in ASSET_CLASSES.items():
        df = yf.download(tickers, start=start_date, progress=False)['Close']
        df.columns = [TICKER_NAMES.get(t, t) for t in df.columns]
        data[cls] = df
    return data

def get_volume_dollar(start_date='2025-01-01'):
    data = {}
    for cls, tickers in ASSET_CLASSES.items():
        df = yf.download(tickers, start=start_date, progress=False)
        # Use 'Volume' * 'Close' but handle NaN/zero better
        dollar_vol = (df['Volume'] * df['Close']).fillna(0)
        # Average across tickers in the class
        avg_dollar_vol = dollar_vol.mean(axis=1)
        data[cls] = avg_dollar_vol.to_frame(name=f'{cls}_liquidity')
    return pd.concat(data.values(), axis=1)

def get_market_caps():
    caps = {}
    for cls, tickers in ASSET_CLASSES.items():
        cls_caps = {}
        for t in tickers:
            if t in ['EURUSD=X', 'USDJPY=X']:
                continue
            try:
                info = yf.Ticker(t).info
                cap = info.get('marketCap') or info.get('totalMarketCap') or info.get('enterpriseValue')
                if cap and cap > 0:
                    cls_caps[TICKER_NAMES.get(t, t)] = cap
            except:
                pass  # silent fail for flaky tickers
        if cls_caps:
            caps[cls] = cls_caps
    return caps

def format_money(value):
    if pd.isna(value) or value == 0:
        return "N/A"
    if abs(value) >= 1e9:
        return f"${value/1e9:.2f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.1f}M"
    else:
        return f"${value:,.0f}"