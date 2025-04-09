# MarketPulse Analyzer

## 개요

이 프로그램은 사용자가 지정한 주식 티커(예: TSLA, AAPL)에 대해 다양한 기술적 지표를 계산하고, 이를 기반으로 매수(Buy) 또는 매도(Sell) 신호를 제공하는 파이썬 기반 도구입니다. `yfinance`를 통해 주식 데이터를 가져오고, `requests`를 통해 CNN의 Fear & Greed Index를 수집하며, 여러 기술적 지표(RSI, MACD, Bollinger Bands 등)를 분석합니다. 분석 결과는 가중치 기반 점수로 매수/매도 신호를 결정하고, `tabulate`와 `termcolor`를 활용해 콘솔에 깔끔하고 색상 입힌 출력으로 제공됩니다.

이 프로젝트는 주식 시장의 기술적 분석을 자동화하고, 투자 의사결정을 보조하기 위한 교육적 목적으로 설계되었습니다.

## 주요 기능

### 데이터 수집
- **Fear & Greed Index**: CNN의 API에서 시장 심리를 나타내는 Fear & Greed Index를 가져옵니다.
- **VIX**: 변동성 지수(VIX)를 `yfinance`로 수집하여 시장 불안정성을 평가합니다.
- **주식 데이터**: `yfinance`를 통해 지정된 티커의 과거 2년간 OHLCV(Open, High, Low, Close, Volume) 데이터를 가져옵니다.

### 기술적 지표 계산
- **RSI (Relative Strength Index)**: 5일, 14일, 주간 RSI를 계산하여 과매수/과매도 상태를 판단합니다.
- **MACD (Moving Average Convergence Divergence)**: MACD, Signal, Histogram을 계산해 추세 전환을 감지합니다.
- **Stochastic Oscillator**: %K 값을 통해 단기 과매수/과매도 상태를 확인합니다.
- **Bollinger Bands**: 20일 이동평균과 표준편차로 변동성을 측정하고, 밴드 폭을 계산합니다.
- **SMA (Simple Moving Average)**: 5일, 10일, 50일, 200일 SMA로 단기 및 장기 추세를 분석합니다.
- **VWAP (Volume Weighted Average Price)**: 거래량 가중 평균 가격으로 주가의 상대적 위치를 평가합니다.
- **ATR (Average True Range)**: 14일 평균 진폭으로 시장 변동성을 측정합니다.
- **OBV (On-Balance Volume)**: 거래량을 통해 매수/매도 압력을 분석합니다.
- **Volume Change**: 거래량 변화율을 계산하여 시장 참여도를 확인합니다.

### 신호 생성
- 각 지표에 대해 미리 정의된 조건을 평가하여 매수 및 매도 신호를 생성합니다.
- 가중치를 적용해 신호의 강도를 점수화하고, 최종 추천(Buy, Sell, Hold)을 결정합니다.

### 출력
- 분석 결과를 카테고리(Momentum, Volatility, Trend, Volume)별로 정리하여 표 형식으로 출력합니다.
- `tabulate`로 깔끔한 표를 그리고, `termcolor`로 색상을 입혀 가독성을 높입니다.
- 매수/매도 신호와 추천 결과를 강조 표시합니다.

## 설치 및 실행

### Prerequisites
- **Python 버전**: 3.6 이상
- **필요한 라이브러리**:
  - `requests`: Fear & Greed Index API 호출
  - `pandas`: 데이터 처리 및 분석
  - `yfinance`: 주식 및 VIX 데이터 수집
  - `tabulate`: 표 형식 출력
  - `termcolor`: 콘솔 출력 색상화
  - `rich`: 콘솔 출력 개선 (선택적)

### 설치 방법
1. 필요한 라이브러리를 설치합니다:
   ```bash
   pip install requests pandas yfinance tabulate termcolor rich
   ```
2. GitHub에서 코드를 다운로드하거나 클론합니다:
   ```bash
   git clone https://github.com/pjhwa/mi.git
   cd mi
   ```

### 실행 방법
1. 터미널에서 다음 명령어로 프로그램을 실행합니다:
   ```bash
   python mpa.py --tickers TSLA,AAPL
   ```
   - `--tickers`: 분석할 주식 티커를 쉼표로 구분해 지정 (기본값: `TSLA`)
2. 지정된 티커에 대한 지표 분석과 매수/매도 신호가 콘솔에 출력됩니다.

## 코드 구조

### 데이터 수집
- **`get_fear_greed_data()`**: CNN API에서 Fear & Greed Index를 가져오며, 최근 2년 데이터를 요청합니다. 오류 발생 시 `None` 반환.
- **`get_vix_data()`**: `yfinance`로 VIX 지수의 최신 종가를 가져옵니다.
- **`get_stock_data(ticker)`**: 지정된 티커의 2년간 주식 데이터를 가져와 DataFrame으로 반환합니다.

### 지표 계산
- **`calculate_rsi(df, period)`**: 지정된 기간(기본 14일) RSI를 계산합니다.
- **`calculate_macd(df)`**: MACD, Signal, Histogram을 계산합니다.
- **`calculate_bollinger_bands(df, period)`**: 20일 SMA와 상하 밴드, 밴드 폭을 계산합니다.
- **`calculate_sma(df, period)`**: 지정된 기간의 단순 이동평균을 계산합니다.
- **`calculate_stochastic_oscillator(df, period)`**: 14일 Stochastic %K를 계산합니다.
- **`calculate_obv(df)`**: OBV를 계산해 거래량 흐름을 분석합니다.
- **`calculate_atr(df, period)`**: 14일 ATR로 변동성을 측정합니다.
- **`calculate_vwap(df)`**: 일별 VWAP를 계산합니다.
- **`calculate_volume_change(df)`**: 거래량 변화율을 계산합니다.
- **`calculate_weekly_rsi(df, period)`**: 주간 데이터를 생성해 RSI를 계산합니다.
- **`calculate_all_indicators(df)`**: 모든 지표를 한꺼번에 계산하여 DataFrame에 추가합니다.

### 신호 생성
- **`generate_signals(df, fear_greed, vix)`**: 최신 데이터를 기반으로 매수/매도 신호를 생성하고, 가중치 점수를 계산합니다.
  - **가중치**: Fear & Greed(0.05), RSI(0.15), MACD(0.15), Stochastic(0.1), Volume Change(0.1), BB Width(0.1), SMA(0.2), VWAP(0.1)

### 출력
- **`display_market_indicators(df_dict, fear_greed, vix)`**: 티커별로 지표와 신호를 카테고리별 표로 출력하고, 추천 결과를 강조합니다.

### 메인 함수
- **`main()`**: 명령줄 인수(티커)를 파싱하고, 데이터를 수집/분석하여 결과를 출력합니다.

## 사용 예시

### 실행 명령어
```bash
python mpa.py --tickers TSLA,AAPL
```

### 출력 예시
```
======================================================
📈 Market Indicators Summary for TSLA (2023-10-15)
======================================================

📊 Momentum
╒════════════════════╤═════════╤═════════════════════════╕
│ Indicator          │   Value │ Trend/Notes             │
╞════════════════════╪═════════╪═════════════════════════╡
│ Fear & Greed Index │   18.00 │ 극단적 공포 (매수 기회) │
├────────────────────┼─────────┼─────────────────────────┤
│ MACD Histogram     │   -0.10 │ 하락 중 (음수: Bearish) │
├────────────────────┼─────────┼─────────────────────────┤
│ Daily RSI          │   35.73 │ 하락 중 (중립)          │
├────────────────────┼─────────┼─────────────────────────┤
│ Weekly RSI         │   37.21 │ 하락 중 (중립)          │
├────────────────────┼─────────┼─────────────────────────┤
│ Short RSI          │   23.03 │ 하락 중 (≤30: Oversold) │
╘════════════════════╧═════════╧═════════════════════════╛

📊 Volatility
╒═════════════╤═════════╤═════════════════════╕
│ Indicator   │ Value   │ Trend/Notes         │
╞═════════════╪═════════╪═════════════════════╡
│ ATR         │ $23.01  │ 낮은 변동성         │
├─────────────┼─────────┼─────────────────────┤
│ BB Width    │ 0.31    │ 높은 변동성 (>0.15) │
├─────────────┼─────────┼─────────────────────┤
│ VIX         │ 49.08   │ 시장 불안 (>30)     │
╘═════════════╧═════════╧═════════════════════╛

📊 Trend
╒═════════════╤═════════╤═════════════════════════════════╕
│ Indicator   │ Value   │ Trend/Notes                     │
╞═════════════╪═════════╪═════════════════════════════════╡
│ TSLA Close  │ $221.86 │ 하락 추세 (SMA50 아래)          │
├─────────────┼─────────┼─────────────────────────────────┤
│ SMA5        │ $248.92 │ 하락 중 (SMA10 아래: 단기 하락) │
├─────────────┼─────────┼─────────────────────────────────┤
│ SMA50       │ $300.01 │ 하락 중 (SMA200 위: 장기 상승)  │
├─────────────┼─────────┼─────────────────────────────────┤
│ SMA200      │ $289.20 │ 상승 중 (Close 아래: 장기 하락) │
╘═════════════╧═════════╧═════════════════════════════════╛

📊 Volume
╒═══════════════╤════════════╤═══════════════════════════╕
│ Indicator     │ Value      │ Trend/Notes               │
╞═══════════════╪════════════╪═══════════════════════════╡
│ Volume Change │ -7.30%     │ 하락 중 (감소: 매도 압력) │
├───────────────┼────────────┼───────────────────────────┤
│ OBV           │ 2464678200 │ 하락 중 (매도 압력 증가)  │
├───────────────┼────────────┼───────────────────────────┤
│ VWAP          │ $241.91    │ 하락 추세 (Close 아래)    │
╘═══════════════╧════════════╧═══════════════════════════╛

📌 Buy & Sell Signals
🟢 Buy Signals (weighted points: 0.30):
   • Fear & Greed Index ≤ 20 (Extreme Fear)
   • Short RSI ≤ 30 (Oversold)
   • Stochastic %K ≤ 20 (Oversold)

🔴 Sell Signals (weighted points: 0.55):
   • MACD Histogram < 0 (Bearish)
   • BB Width > 0.15 (High Volatility)
   • SMA5 < SMA10 (Bearish)
   • Close < VWAP (Bearish)

📍 ATR: 23.01 | VIX: 49.08

💡 Recommendation: Sell
📢 Explanation: ⚠️ 매도 신호가 매수 신호보다 강함 (Buy Points: 0.30, Sell Points: 0.55)
```

## 지표 설명

- **Fear & Greed Index**: 시장 심리를 나타내며, ≤20은 극단적 공포(매수 기회), ≥81은 극단적 탐욕(매도 신호)로 해석됩니다.
- **RSI**: 과매수(≥70) 또는 과매도(≤30) 상태를 측정합니다.
- Grande MACD Histogram**: MACD와 Signal의 차이로, 양수는 상승(Bullish), 음수는 하락(Bearish) 추세를 의미합니다.
- **Stochastic Oscillator**: %K가 ≤20은 과매도, ≥80은 과매수 상태를 나타냅니다.
- **Bollinger Bands**: 밴드 폭(BB Width)이 클수록 변동성이 높고, 작을수록 안정적입니다.
- **SMA**: 단기 SMA(SMA5, SMA10)가 장기 SMA(SMA50, SMA200)와의 상대적 위치로 추세를 판단합니다.
- **VWAP**: 주가가 VWAP 위면 상승, 아래면 하락 추세로 해석됩니다.
- **ATR**: 높은 값은 큰 변동성을, 낮은 값은 안정성을 의미합니다.
- **OBV**: OBV 상승은 매수 압력, 하락은 매도 압력을 나타냅니다.
- **Volume Change**: 거래량 증가(>50%)는 강한 매수, 감소(<-10%)는 매도 신호로 간주됩니다.

## 가중치 설정

매수/매도 신호의 강도를 점수화하기 위해 각 지표에 다음 가중치를 적용합니다:

| 지표                  | 가중치 |
|-----------------------|--------|
| Fear & Greed Index    | 0.05   |
| RSI                   | 0.15   |
| MACD                  | 0.15   |
| Stochastic Oscillator | 0.10   |
| Volume Change         | 0.10   |
| Bollinger Band Width  | 0.10   |
| SMA                   | 0.20   |
| VWAP                  | 0.10   |

- **조정 가능**: 가중치는 사용자의 투자 전략에 따라 수정할 수 있습니다.

## 주의사항

- **교육 목적**: 이 프로그램은 분석 도구로 설계되었으며, 실제 투자 결정 시 금융 전문가와 상담하세요.
- **데이터 의존성**: `yfinance`와 CNN API에 의존하므로, 데이터 오류나 API 실패 시 결과가 영향을 받을 수 있습니다.
- **API 오류 처리**: Fear & Greed Index 요청 실패 시 `N/A`로 표시되며, 프로그램은 중단되지 않습니다.
- **실시간성**: 데이터는 `yfinance`의 최신 업데이트에 따라 달라질 수 있습니다.
