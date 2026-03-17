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

# 2. 상단 헤더 및 실시간 매크로 지표
st.title("🚀 Professional 주식 통합 분석 대시보드")
try:
    usd_krw_ticker = yf.Ticker("USDKRW=X")
    usd_krw = usd_krw_ticker.history(period="1d")['Close'].iloc[-1]
    st.info(f"🌐 **실시간 환율 정보:** 1달러 = {round(usd_krw, 1)}원")
except Exception:
    st.write("환율 정보를 불러오는 중...")

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
    st.caption("Tip: 한국 주식은 .KS(코스피) 또는 .KQ(코스닥)를 붙이세요.")

# 4. 메인 분석 엔진
if st.button("Deep Analysis 실행"):
    try:
        with st.spinner('실시간 데이터를 정밀 분석 중입니다...'):
            stock = yf.Ticker(selected_ticker)
            df = stock.history(period="1y")
            info = stock.info
            
            if df.empty:
                st.error("데이터를 가져오지 못했습니다. 종목 코드를 다시 확인해 주세요.")
            else:
                # --- 데이터 가공 ---
                curr_price = df['Close'].iloc[-1]
                per = info.get('trailingPE') or info.get('forwardPE') or 0
                pbr = info.get('priceToBook') or 0
                roe = (info.get('returnOnEquity') or 0) * 100
                
                df['RSI'] = ta.rsi(df['Close'], length=14)
                bbands = ta.bbands(df['Close'], length=20, std=2)
                df = pd.concat([df, bbands], axis=1)
                
                target_mean = info.get('targetMeanPrice') or curr_price
                recommendation = (info.get('recommendationKey') or "N/A").upper()
                upside = ((target_mean / curr_price) - 1) * 100 if target_mean else 0

                # 종합 점수 (5점 만점)
                score = 0
                if roe >= 10: score += 1
                if 0 < per <= 15: score += 1
                if 0 < pbr <= 1.2: score += 1
                if df['RSI'].iloc[-1] <= 45: score += 1
                if upside >= 15: score += 1

                # --- 화면 출력 ---
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("현재가", f"{round(curr_price, 2):,}")
                m2.metric("종합 점수", f"{score}/5")
                m3.metric("RSI (심리)", f"{round(df['RSI'].iloc[-1], 1)}")
                m4.metric("ROE (수익성)", f"{round(roe, 1)}%")
                m5.metric("상승여력", f"{round(upside, 1)}%")

                # 차트 섹션
                st.subheader("📊 기술적 분석 차트")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='주가'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], line=dict(color='rgba(200, 200, 200, 0.5)'), name='Upper BB'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], line=dict(color='rgba(200, 200, 200, 0.5)'), fill='tonexty', name='Lower BB'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='orange'), name='RSI'), row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                fig.update_layout(height=600, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

                col_left, col_right = st.columns(2)
                with col_left:
                    st.subheader("💡 투자 가이드라인")
                    st.success(f"✅ **적정 매수 범위:** {round(curr_price * 0.93, 2):,} ~ {round(curr_price * 0.98, 2):,}")
                    st.warning(f"🚀 **목표 매도가:** {round(target_mean, 2):,}")
                    st.write(f"📊 **밸류:** PER {round(per, 1) if per else 'N/A'} / PBR {round(pbr, 1) if pbr else 'N/A'}")
                
                with col_right:
                    st.subheader("👨‍🏫 전문가 분석")
                    st.write(f"📢 **추천 등급:** {recommendation}")
                    st.write(f"🎯 **의견:** 현재가 대비 {round(upside, 1)}% 상승 전망")

                st.subheader("📰 최신 뉴스")
                if stock.news:
                    for n in stock.news[:5]:
                        with st.expander(n['title']):
                            st.write(f"발행처: {n['publisher']} | [기사보기]({n['link']})")
                else:
                    st.info("뉴스가 없습니다.")

    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
