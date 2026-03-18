import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정 및 세션 관리
st.set_page_config(page_title="Professional Stock Analyzer", layout="wide")

if 'my_list' not in st.session_state:
    st.session_state['my_list'] = ["005930.KS", "000660.KS", "NVDA", "TSLA", "AAPL"]

# 2. 상단 헤더 및 실시간 환율
st.title("🚀 Professional 주식 통합 분석 대시보드")
try:
    usd_krw_ticker = yf.Ticker("USDKRW=X")
    usd_krw_df = usd_krw_ticker.history(period="1d")
    if not usd_krw_df.empty:
        usd_krw = usd_krw_df['Close'].iloc[-1]
        st.info(f"🌐 **실시간 환율 정보:** 1달러 = {round(usd_krw, 1)}원")
except Exception:
    pass

# 3. 사이드바: 종목 관리
with st.sidebar:
    st.header("📋 포트폴리오 관리")
    new_ticker = st.text_input("종목 코드 추가 (예: AAPL, 005930.KS)").upper()
    if st.button("목록에 추가"):
        if new_ticker and new_ticker not in st.session_state['my_list']:
            st.session_state['my_list'].append(new_ticker)
            st.rerun()
    
    if st.button("목록 초기화"):
        st.session_state['my_list'] = ["005930.KS", "NVDA"]
        st.rerun()
    
    st.write("---")
    selected_ticker = st.selectbox("분석할 종목을 선택하세요", st.session_state['my_list'])

# 4. 메인 분석 엔진
if st.button("Deep Analysis 실행"):
    try:
        with st.spinner('실시간 데이터를 분석 중입니다...'):
            stock = yf.Ticker(selected_ticker)
            # 볼린저 밴드 계산을 위해 충분한 데이터(1년) 확보
            df = stock.history(period="1y")
            
            if df.empty or len(df) < 20:
                st.error("데이터가 부족합니다. 종목 코드를 확인하거나 상장 기간을 확인해 주세요.")
            else:
                info = stock.info
                curr_price = df['Close'].iloc[-1]
                
                # --- 기술 지표 계산 및 안전한 병합 ---
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                # 볼린저 밴드 계산 (이름 충돌 방지를 위해 명시적 처리)
                bb = ta.bbands(df['Close'], length=20, std=2)
                if bb is not None:
                    # 기존 데이터에 볼린저 밴드 데이터프레임을 가로로 합침
                    df = pd.concat([df, bb], axis=1)
                
                # 재무 데이터 추출
                roe = info.get('returnOnEquity')
                if roe: roe = roe * 100
                target_mean = info.get('targetMeanPrice')
                upside = ((target_mean / curr_price) - 1) * 100 if target_mean else 0

                # --- 지표 상단 레이아웃 ---
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("현재가", f"{round(curr_price, 2):,}")
                m2.metric("RSI (심리)", round(df['RSI'].iloc[-1], 1) if not pd.isna(df['RSI'].iloc[-1]) else "N/A")
                m3.metric("ROE", f"{round(roe, 1)}%" if roe else "N/A")
                m4.metric("상승여력", f"{round(upside, 1)}%" if upside else "N/A")

                # --- 차트 그리기 (오류 방지 로직 포함) ---
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                   vertical_spacing=0.05, row_heights=[0.7, 0.3])
                
                # 1단: 캔들스틱
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                            low=df['Low'], close=df['Close'], name='주가'), row=1, col=1)
                
                # 볼린저 밴드 컬럼이 존재하는지 확인 후 그리기
                upper_col = 'BBU_20_2.0'
                lower_col = 'BBL_20_2.0'
                
                if upper_col in df.columns and lower_col in df.columns:
                    fig.add_trace(go.Scatter(x=df.index, y=df[upper_col], 
                                             line=dict(color='rgba(200, 200, 200, 0.4)'), name='상단 밴드'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df[lower_col], 
                                             line=dict(color='rgba(200, 200, 200, 0.4)'), 
                                             fill='tonexty', name='하단 밴드'), row=1, col=1)
                
                # 2단: RSI
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='orange'), name='RSI'), row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                
                fig.update_layout(height=600, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

                # 뉴스 섹션
                st.subheader("📰 최신 관련 뉴스")
                if stock.news:
                    for n in stock.news[:3]:
                        st.write(f"• [{n['title']}]({n['link']})")
                else:
                    st.write("관련 뉴스가 없습니다.")

    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
        st.info("Tip: 데이터 로드 문제일 수 있습니다. 잠시 후 다시 시도해 보세요.")
