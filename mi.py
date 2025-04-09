import requests
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import argparse
from tabulate import tabulate
from termcolor import colored
from rich.console import Console
from rich.text import Text

console = Console()

# Fear & Greed Index 데이터 수집 및 저장 (수정된 함수)
def get_fear_greed_data():
    """Fear & Greed Index 데이터를 가져와 저장하고 최신 값을 반환합니다."""
    today = datetime.now()
    start_date = today - timedelta(days=730)
    start_date_str = start_date.strftime('%Y-%m-%d')
    url = f'https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{start_date_str}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        df = pd.json_normalize(data['fear_and_greed_historical']['data'])
        df['date'] = pd.to_datetime(df['x'], unit='ms').dt.date
        df = df[['date', 'y']].rename(columns={'y': 'fear_greed_index'})
        return df['fear_greed_index'].iloc[-1]  # 최신 값 반환
    except Exception as e:
        print(f"Fear & Greed Index 가져오기 실패: {e}")
        return None

def get_vix_data():
    vix_df = yf.download("^VIX", period="1d", interval="1d", progress=False, auto_adjust=False)
    if vix_df.empty:
        return None
    return vix_df['Close'].iloc[-1]

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="2y", auto_adjust=False, actions=False)
    if df.empty:
        return None
    df = df.reset_index()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]

# 지표 계산 함수 (생략 - 변경 없음)
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    for i in range(period, len(df)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + loss.iloc[i]) / period
    rs = avg_gain / avg_loss
    df[f'RSI_{period}'] = 100 - ( 100 / (1 + rs))
    return df

def calculate_macd(df):
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['Signal']
    return df

def calculate_bollinger_bands(df, period=20):
    df['SMA20'] = df['Close'].rolling(window=period).mean()
    df['STD20'] = df['Close'].rolling(window=period).std()
    df['Upper_Band'] = df['SMA20'] + (2 * df['STD20'])
    df['Lower_Band'] = df['SMA20'] - (2 * df['STD20'])
    df['BB_Width'] = (df['Upper_Band'] - df['Lower_Band']) / df['SMA20']
    return df

def calculate_sma(df, period):
    df[f'SMA{period}'] = df['Close'].rolling(window=period).mean()
    return df

def calculate_stochastic_oscillator(df, period=14):
    df['Lowest_Low'] = df['Low'].rolling(window=period).min()
    df['Highest_High'] = df['High'].rolling(window=period).max()
    df['Percent_K'] = (df['Close'] - df['Lowest_Low']) / (df['Highest_High'] - df['Lowest_Low']) * 100
    return df

def calculate_obv(df):
    df['OBV'] = (df['Volume'] * (df['Close'].diff() > 0).astype(int) - df['Volume'] * (df['Close'].diff() < 0).astype(int)).cumsum()
    return df

def calculate_atr(df, period=14):
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=period).mean()
    return df

def calculate_vwap(df):
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    return df

def calculate_volume_change(df):
    df['Volume_Change'] = df['Volume'].pct_change()
    return df

def calculate_weekly_rsi(df, period=14):
    df_weekly = df.resample('W').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    return calculate_rsi(df_weekly, period).rename(columns={f'RSI_{period}': 'Weekly_RSI'})['Weekly_RSI']

def calculate_all_indicators(df):
    df = calculate_rsi(df, 14)
    df = calculate_rsi(df, 5)
    df = calculate_macd(df)
    df = calculate_bollinger_bands(df)
    df = calculate_sma(df, 5)
    df = calculate_sma(df, 10)
    df = calculate_sma(df, 50)
    df = calculate_sma(df, 200)
    df = calculate_stochastic_oscillator(df)
    df = calculate_obv(df)
    df = calculate_atr(df)
    df = calculate_vwap(df)
    df = calculate_volume_change(df)
    weekly_rsi = calculate_weekly_rsi(df)
    df['Weekly_RSI'] = weekly_rsi.reindex(df.index, method='ffill')
    return df

# 신호 생성 함수
def generate_signals(df, fear_greed, vix):
    latest = df.iloc[-1]
    buy_signals = []
    sell_signals = []
    buy_points = 0.0
    sell_points = 0.0

    weights = {
        'fear_greed': 0.05,
        'rsi': 0.15,
        'macd': 0.15,
        'stochastic': 0.1,
        'volume_change': 0.1,
        'bb_width': 0.1,
        'sma': 0.2,
        'vwap': 0.1
    }

    if fear_greed is not None:
        if fear_greed <= 20:
            buy_signals.append("Fear & Greed Index ≤ 20 (Extreme Fear)")
            buy_points += weights['fear_greed']
        elif fear_greed >= 81:
            sell_signals.append("Fear & Greed Index ≥ 81 (Extreme Greed)")
            sell_points += weights['fear_greed']

    if latest['RSI_14'] <= 30:
        buy_signals.append("Daily RSI ≤ 30 (Oversold)")
        buy_points += weights['rsi']
    elif latest['RSI_14'] >= 70:
        sell_signals.append("Daily RSI ≥ 70 (Overbought)")
        sell_points += weights['rsi']
    if latest['Weekly_RSI'] <= 30:
        buy_signals.append("Weekly RSI ≤ 30 (Oversold)")
        buy_points += weights['rsi']
    elif latest['Weekly_RSI'] >= 70:
        sell_signals.append("Weekly RSI ≥ 70 (Overbought)")
        sell_points += weights['rsi']
    if latest['RSI_5'] <= 30:
        buy_signals.append("Short RSI ≤ 30 (Oversold)")
        buy_points += weights['rsi']
    elif latest['RSI_5'] >= 70:
        sell_signals.append("Short RSI ≥ 70 (Overbought)")
        sell_points += weights['rsi']

    if latest['MACD_Histogram'] > 0:
        buy_signals.append("MACD Histogram > 0 (Bullish)")
        buy_points += weights['macd']
    elif latest['MACD_Histogram'] < 0:
        sell_signals.append("MACD Histogram < 0 (Bearish)")
        sell_points += weights['macd']

    if latest['Percent_K'] <= 20:
        buy_signals.append("Stochastic %K ≤ 20 (Oversold)")
        buy_points += weights['stochastic']
    elif latest['Percent_K'] >= 80:
        sell_signals.append("Stochastic %K ≥ 80 (Overbought)")
        sell_points += weights['stochastic']

    if latest['Volume_Change'] > 0.5:
        buy_signals.append("Volume Change > 50% (Strong Buy)")
        buy_points += weights['volume_change']
    elif latest['Volume_Change'] < -0.1:
        sell_signals.append("Volume Change < -10% (Sell)")
        sell_points += weights['volume_change']

    if latest['BB_Width'] < 0.05:
        buy_signals.append("BB Width < 0.05 (Low Volatility)")
        buy_points += weights['bb_width']
    elif latest['BB_Width'] > 0.15:
        sell_signals.append("BB Width > 0.15 (High Volatility)")
        sell_points += weights['bb_width']

    if latest['SMA5'] > latest['SMA10']:
        buy_signals.append("SMA5 > SMA10 (Bullish)")
        buy_points += weights['sma']
    elif latest['SMA5'] < latest['SMA10']:
        sell_signals.append("SMA5 < SMA10 (Bearish)")
        sell_points += weights['sma']

    if latest['Close'] > latest['VWAP']:
        buy_signals.append("Close > VWAP (Bullish)")
        buy_points += weights['vwap']
    elif latest['Close'] < latest['VWAP']:
        sell_signals.append("Close < VWAP (Bearish)")
        sell_points += weights['vwap']

    return buy_signals, sell_signals, buy_points, sell_points

# 출력 함수
def display_market_indicators(df_dict, fear_greed, vix):
    current_date = datetime.now().strftime('%Y-%m-%d')
    for ticker, df in df_dict.items():
        if df is None or df.empty:
            print(f"No data available for {ticker}.")
            continue

        latest = df.iloc[-1]
        prev = df.iloc[-3] if len(df) >= 3 else df.iloc[0]  # 3일 전 데이터

        indicators = {
            'Momentum': [
                {'Indicator': 'Fear & Greed Index', 'Value': f"{fear_greed:.2f}" if fear_greed else 'N/A',
                 'Trend/Notes': '극단적 공포 (매수 기회)' if fear_greed and fear_greed <= 20 else '극단적 탐욕 (매도 신호)' if fear_greed and fear_greed >= 81 else '중립'},
                {'Indicator': 'MACD Histogram', 'Value': f"{latest['MACD_Histogram']:.2f}",
                 'Trend/Notes': f"{'상승 중' if latest['MACD_Histogram'] > prev['MACD_Histogram'] else '하락 중'} (양수: Bullish)" if latest['MACD_Histogram'] > 0 else f"{'상승 중' if latest['MACD_Histogram'] > prev['MACD_Histogram'] else '하락 중'} (음수: Bearish)"},
                {'Indicator': 'Daily RSI', 'Value': f"{latest['RSI_14']:.2f}",
                 'Trend/Notes': f"{'상승 중' if latest['RSI_14'] > prev['RSI_14'] else '하락 중'} (≤30: Oversold)" if latest['RSI_14'] <= 30 else f"{'상승 중' if latest['RSI_14'] > prev['RSI_14'] else '하락 중'} (≥70: Overbought)" if latest['RSI_14'] >= 70 else f"{'상승 중' if latest['RSI_14'] > prev['RSI_14'] else '하락 중'} (중립)"},
                {'Indicator': 'Weekly RSI', 'Value': f"{latest['Weekly_RSI']:.2f}",
                 'Trend/Notes': f"{'상승 중' if latest['Weekly_RSI'] > prev['Weekly_RSI'] else '하락 중'} (≤30: Oversold)" if latest['Weekly_RSI'] <= 30 else f"{'상승 중' if latest['Weekly_RSI'] > prev['Weekly_RSI'] else '하락 중'} (≥70: Overbought)" if latest['Weekly_RSI'] >= 70 else f"{'상승 중' if latest['Weekly_RSI'] > prev['Weekly_RSI'] else '하락 중'} (중립)"},
                {'Indicator': 'Short RSI', 'Value': f"{latest['RSI_5']:.2f}",
                 'Trend/Notes': f"{'상승 중' if latest['RSI_5'] > prev['RSI_5'] else '하락 중'} (≤30: Oversold)" if latest['RSI_5'] <= 30 else f"{'상승 중' if latest['RSI_5'] > prev['RSI_5'] else '하락 중'} (≥70: Overbought)" if latest['RSI_5'] >= 70 else f"{'상승 중' if latest['RSI_5'] > prev['RSI_5'] else '하락 중'} (중립)"},
            ],
            'Volatility': [
                {'Indicator': 'ATR', 'Value': f"${latest['ATR']:.2f}",
                 'Trend/Notes': '높은 변동성' if latest['ATR'] > latest['ATR'].mean() * 1.5 else '낮은 변동성'},
                {'Indicator': 'BB Width', 'Value': f"{latest['BB_Width']:.2f}",
                 'Trend/Notes': '높은 변동성 (>0.15)' if latest['BB_Width'] > 0.15 else '낮은 변동성 (<0.05)'},
                {'Indicator': 'VIX', 'Value': f"{vix:.2f}" if vix is not None else 'N/A',
                 'Trend/Notes': '시장 불안 (>30)' if vix and vix > 30 else '시장 안정 (<20)' if vix and vix < 20 else '중립'},
            ],
            'Trend': [
                {'Indicator': f'{ticker} Close', 'Value': f"${latest['Close']:.2f}",
                 'Trend/Notes': '상승 추세 (SMA50 위)' if latest['Close'] > latest['SMA50'] else '하락 추세 (SMA50 아래)'},
                {'Indicator': 'SMA5', 'Value': f"${latest['SMA5']:.2f}",
                 'Trend/Notes': f"{'상승 중' if latest['SMA5'] > prev['SMA5'] else '하락 중'} (SMA10 위: 단기 상승)" if latest['SMA5'] > latest['SMA10'] else f"{'상승 중' if latest['SMA5'] > prev['SMA5'] else '하락 중'} (SMA10 아래: 단기 하락)"},
                {'Indicator': 'SMA50', 'Value': f"${latest['SMA50']:.2f}",
                 'Trend/Notes': f"{'상승 중' if latest['SMA50'] > prev['SMA50'] else '하락 중'} (SMA200 위: 장기 상승)" if latest['SMA50'] > latest['SMA200'] else f"{'상승 중' if latest['SMA50'] > prev['SMA50'] else '하락 중'} (SMA200 아래: 장기 하락)"},
                {'Indicator': 'SMA200', 'Value': f"${latest['SMA200']:.2f}",
                 'Trend/Notes': f"{'상승 중' if latest['SMA200'] > prev['SMA200'] else '하락 중'} (Close 위: 장기 상승)" if latest['Close'] > latest['SMA200'] else f"{'상승 중' if latest['SMA200'] > prev['SMA200'] else '하락 중'} (Close 아래: 장기 하락)"},
            ],
            'Volume': [
                {'Indicator': 'Volume Change', 'Value': f"{latest['Volume_Change']:.2%}",
                 'Trend/Notes': f"{'상승 중' if latest['Volume_Change'] > prev['Volume_Change'] else '하락 중'} (증가: 매수 압력)" if latest['Volume_Change'] > 0 else f"{'상승 중' if latest['Volume_Change'] > prev['Volume_Change'] else '하락 중'} (감소: 매도 압력)"},
                {'Indicator': 'OBV', 'Value': f"{latest['OBV']:.0f}",
                 'Trend/Notes': f"{'상승 중' if latest['OBV'] > prev['OBV'] else '하락 중'} (매수 압력 증가)" if latest['OBV'] > prev['OBV'] else f"{'상승 중' if latest['OBV'] > prev['OBV'] else '하락 중'} (매도 압력 증가)"},
                {'Indicator': 'VWAP', 'Value': f"${latest['VWAP']:.2f}",
                 'Trend/Notes': '상승 추세 (Close 위)' if latest['Close'] > latest['VWAP'] else '하락 추세 (Close 아래)'},
            ]
        }

        title = f"📈 Market Indicators Summary for {ticker} ({current_date})"
        print(f"\n{colored('='*len(title), 'cyan')}")
        print(colored(title, 'green', attrs=['bold']))
        print(f"{colored('='*len(title), 'cyan')}\n")

        for category, ind_list in indicators.items():
            print(colored(f"📊 {category}", 'magenta', attrs=['bold']))
            print(tabulate(pd.DataFrame(ind_list), headers=['Indicator', 'Value', 'Trend/Notes'], tablefmt='fancy_grid', showindex=False))
            print()

        buy_signals, sell_signals, buy_points, sell_points = generate_signals(df, fear_greed, vix)
        recommendation = "Buy" if buy_points > sell_points else "Sell" if sell_points > buy_points else "Hold"
        rec_color = 'green' if recommendation == "Buy" else 'red' if recommendation == "Sell" else 'yellow'

        print(colored("📌 Buy & Sell Signals", 'cyan', attrs=['bold']))
        print(f"🟢 Buy Signals (weighted points: {buy_points:.2f}):")
        for signal in buy_signals if buy_signals else ["None"]:
            print(f"   • {signal}")
        print(f"\n🔴 Sell Signals (weighted points: {sell_points:.2f}):")
        for signal in sell_signals if sell_signals else ["None"]:
            print(f"   • {signal}")

        vix_str = f"{vix:.2f}" if vix is not None else 'N/A'
        print(f"\n📍 ATR: {latest['ATR']:.2f} | VIX: {vix_str}")

        print("\n" + colored(f"💡 Recommendation: {recommendation}", rec_color, attrs=['bold']))
        explanation = (
            "✅ 매수 신호가 매도 신호보다 강함"
            if buy_points > sell_points else
            "⚠️ 매도 신호가 매수 신호보다 강함"
            if sell_points > buy_points else
            "〰️ 매수와 매도 신호가 균형을 이룸"
        )
        print(colored(f"📢 Explanation: {explanation} (Buy Points: {buy_points:.2f}, Sell Points: {sell_points:.2f})", attrs=['bold']))

# 메인 함수
def main():
    parser = argparse.ArgumentParser(description='Daily Market Indicators Summary')
    parser.add_argument('--tickers', type=str, default='TSLA', help='Comma-separated stock tickers (e.g., TSLA,AAPL)')
    args = parser.parse_args()
    tickers = args.tickers.split(',')

    fear_greed = get_fear_greed_data()
    vix = get_vix_data()
    if isinstance(vix, pd.Series) and not vix.empty:
        vix = vix.iloc[-1]
    elif isinstance(vix, pd.Series) and vix.empty:
        vix = None
    df_dict = {}

    for ticker in tickers:
        df = get_stock_data(ticker)
        if df is not None:
            df = calculate_all_indicators(df)
            df_dict[ticker] = df

    if not df_dict:
        print("No data available for any ticker.")
        return

    display_market_indicators(df_dict, fear_greed, vix)

if __name__ == "__main__":
    main()
