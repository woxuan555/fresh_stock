def auto_code(s):
    s = s.strip()
    if s.upper() in NAME_TO_CODE: return NAME_TO_CODE[s.upper()]
    if s.isdigit() and len(s) == 4:
        # 簡易判斷：通常 4 碼為台股，需補上 .TW
        return s + ".TW"
    return s.upper()

def get_performance_list():
    """抓取清單中股票過去一週的漲跌幅"""
    performance = []
    for code in SCAN_LIST:
        try:
            temp_df = yf.download(code, period="10d", interval="1d", progress=False, auto_adjust=True)
            if len(temp_df) >= 6:
                # 計算過去 5 個交易日的漲跌幅
                start_p = float(temp_df['Close'].iloc[-6])
                end_p = float(temp_df['Close'].iloc[-1])
                pct_change = ((end_p - start_p) / start_p) * 100
                performance.append({"代碼": code, "漲跌幅": round(pct_change, 2), "現價": round(end_p, 2)})
        except:
            continue
    return pd.DataFrame(performance)

import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# --- 1. 資料轉換字典 ---
NAME_TO_CODE = {
    "台積電":"2330.TW","台積":"2330.TW","鴻海":"2317.TW","聯發科":"2454.TW",
    "南亞":"1303.TW","南亞科":"2408.TW","富采":"4772.TW","0050":"0050.TW","0056":"0056.TW",
    "輝達":"NVDA","特斯拉":"TSLA"
}

# --- 2. 頁面設定 ---
st.set_page_config(page_title="股票新手觀察站", layout="wide")

# --- 3. 側邊欄：控制面板 ---
st.sidebar.title("🛠️ 練習控制台")

# 功能 A：代碼與週期
target_input = st.sidebar.text_input("輸入股票名稱或代碼", "2330")
real_code = auto_code(target_input)

time_frame = st.sidebar.selectbox("選擇時間週期", ["日 (Daily)", "週 (Weekly)", "月 (Monthly)"])
tf_map = {"日 (Daily)": "1d", "週 (Weekly)": "1wk", "月 (Monthly)": "1mo"}

# 功能 B：指標開關
st.sidebar.subheader("📈 技術指標顯示")
show_ma5 = st.sidebar.checkbox("顯示 5MA", value=True)
show_ma20 = st.sidebar.checkbox("顯示 20MA", value=True)
show_bb = st.sidebar.checkbox("顯示 布林通道", value=True)
show_rsi = st.sidebar.checkbox("顯示 RSI 圖表", value=True)
show_macd = st.sidebar.checkbox("顯示 MACD (動能)", value=True)

# 功能 C：學習字卡
st.sidebar.divider()
st.sidebar.title("🎓 學習字卡")
topic = st.sidebar.selectbox("觀看指標教學", ["K線圖", "均線 (MA)", "MACD（移動平均收斂散度）" ,"量價關係"])

if topic == "K線圖":
    st.sidebar.info("**紅K（陽線）**：收盤價>開盤價，代表當日多頭佔優。\n"
                    "\n**綠K（陰線）**：收盤價<開盤價，代表空頭壓制。\n"
                    "\n**上影線**長=賣壓強\n\n**下影線**長=買盤撐住。")

elif topic == "均線 (MA)":
    st.sidebar.info("**20MA（月線）**：重要防線，站上=多頭趨勢，跌破=空頭訊號。\n"
                    "\n**5MA（週線）**：短期趨勢參考，\n\n**60MA（季線）**：中期趨勢判斷。\n"
                    "\n**金叉**短期線上穿長期線=買訊\n\n**死叉**長期線上穿短期線=賣訊。")

elif topic == "MACD（移動平均收斂散度）":
    st.sidebar.info("**三要素**："
                    "\n• **DIF（藍線，快線）**：12日EMA-26日EMA，捕捉短期動能\n"
                    "\n• **DEA（黃線，慢線）**：DIF的9日EMA，平滑訊號線\n"
                    "\n• **紅綠柱（Histogram）**：DIF-DEA，柱子變長=動能增強")
    
    # MACD子選單
    sub_topic = st.sidebar.radio("🔍 MACD細節", ["DIF", "DEA", "柱狀圖"])
    
    if sub_topic == "DIF":
        st.sidebar.info("**DIF = 12日EMA - 26日EMA**\n"
                        "\n• DIF上穿0軸=多頭動能增強\n"
                        "\n• DIF下穿0軸=空頭動能增強\n"
                        "\n• 數值越大，趨勢越強烈")
        
    elif sub_topic == "DEA":
        st.sidebar.info("**DEA = DIF的9日EMA**（訊號線）\n"
                        "\n• **DIF上穿DEA**（金叉）=買訊\n"
                        "\n• **DIF下穿DEA**（死叉）=賣訊\n"
                        "\n• DEA過於平緩時，信號較不可靠")
        
    elif sub_topic == "柱狀圖":
        st.sidebar.info("**紅綠柱 = DIF - DEA**（動能柱）\n"
                        "\n• **紅柱變長**：多頭動能增強\n"
                        "\n• **綠柱變長**：空頭動能增強\n"
                        "\n• **柱子縮短**：動能減弱，注意轉折")
        
elif topic == "量價關係":
    st.sidebar.info("**量是水的動力，價是船的高度**")
    
    # 子選單
    v_topic = st.sidebar.radio("🔍 常見組合", ["量增價漲", "量增價跌", "量縮價漲", "量縮價跌", "量縮價跌", "量縮價跌", "量縮價跌", "量縮價跌"])
    if v_topic == "量增價漲":
        st.sidebar.success("【多頭攻擊】\n代表市場認同度高，主力與散戶同步進場，是健康的上升趨勢。")
    elif v_topic == "量增價跌":
        st.sidebar.warning("【恐慌拋售】\n若出現在高檔，小心是大戶倒貨；若在低檔長久下跌後出現，可能是落底換手。")
    elif v_topic == "量縮價漲":
        st.sidebar.error("【動能不足】\n價格雖漲但沒量，代表追價意願薄弱，容易遇到壓力就反轉。")
    elif v_topic == "量縮價漲":
        st.sidebar.error("【動能不足】\n價格雖漲但沒量，代表追價意願薄弱，容易遇到壓力就反轉。")
    elif v_topic == "量縮價漲":
        st.sidebar.error("【動能不足】\n價格雖漲但沒量，代表追價意願薄弱，容易遇到壓力就反轉。")
    elif v_topic == "量縮價漲":
        st.sidebar.error("【動能不足】\n價格雖漲但沒量，代表追價意願薄弱，容易遇到壓力就反轉。")
    elif v_topic == "量縮價漲":
        st.sidebar.error("【動能不足】\n價格雖漲但沒量，代表追價意願薄弱，容易遇到壓力就反轉。")
    elif v_topic == "量縮價漲":
        st.sidebar.error("【動能不足】\n價格雖漲但沒量，代表追價意願薄弱，容易遇到壓力就反轉。")




# --- 4. 主畫面邏輯 ---
st.title(f"🚀 股票練習平台：{target_input} ({real_code})")

try:
    # 抓取資料 (根據不同週期)
    df = yf.download(real_code, period="2y", interval=tf_map[time_frame], auto_adjust=True)
    
    if df.empty:
        st.error("無法抓取資料，請確認代碼是否正確。")
    else:
        # 強制轉為 DataFrame 並壓平 MultiIndex
        df = pd.DataFrame(df)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        #--- MACD
        macd = ta.macd(df['Close'])
        df = pd.concat([df, macd], axis=1)

        #--- 支撐壓力計算
        last_close = float(df["Close"].iloc[-1])
        low20, low60 = df["Low"][-20:].min(), df["Low"][-60:].min()
        high20, high60 = df["High"][-20:].max(), df["High"][-60:].max()
        wave = high60 - low60

        #支撐位
        s1 = round(max(low20, last_close*0.97), 2)
        s2 = round(low60, 2)
        s3 = round(max(30, high60 - wave*1.618), 2)
        # 壓力位
        r1 = round(high20 * 1.005, 2)
        r2 = round(high60 * 1.01, 2)
        r3 = round(high60 + wave*0.618, 2)

        # 計算指標
        df['MA5'] = ta.sma(df['Close'], length=5)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        if show_bb:
            bb = ta.bbands(df['Close'], length=20, std=2)
            df = pd.concat([df, bb], axis=1)

        # 數據摘要
        last_data = df.iloc[-1]
        prev_data = df.iloc[-2]
        curr_p = float(last_data['Close'])
        diff = curr_p - float(prev_data['Close'])
        p_diff = (diff / float(prev_data['Close'])) * 100

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("當前價格", f"{curr_p:.2f}", f"{diff:.2f} ({p_diff:.2f}%)")
        col2.metric("週期最高", f"{last_data['High']:.2f}")
        col3.metric("週期最低", f"{last_data['Low']:.2f}")
        col4.metric("RSI (14)", f"{last_data['RSI']:.2f}" if not pd.isna(last_data['RSI']) else "N/A")


        #--- 支撐壓力字卡區
        st.write("---")
        st.subheader("🛡️ 支撐與壓力位分析 ")
        sup_col, res_col = st.columns(2)
        with sup_col:
            st.success(f"🟢 **支撐區 (買盤力道)**\n\n短期支撐：{s1}\n\n中期支撐：{s2}\n\n強支撐位：{s3}")
        with res_col:
            st.error(f"🔴 **壓力區 (賣壓阻力)**\n\n短期壓力：{r1}\n\n中期壓力：{r2}\n\n強壓力位：{r3}")        

        # --- 繪製主要 K 線圖 ---
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                     low=df['Low'], close=df['Close'], name='K線'))
        
        if show_ma5:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='5MA', line=dict(color='blue', width=1)))
        if show_ma20:
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='20MA', line=dict(color='orange', width=1.5)))
        if show_bb and f'BBU_20_2.0' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], name='布林上軌', line=dict(dash='dash', color='rgba(200,200,200,0.5)')))
            fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], name='布林下軌', line=dict(dash='dash', color='rgba(200,200,200,0.5)')))

        fig.add_hline(y=s1, line_dash="dot",line_color="green",annotation_text="短期支撐")
        fig.add_hline(y=r1, line_dash="dot",line_color="red",annotation_text="短期壓力")

        fig.update_layout(xaxis_rangeslider_visible=False, height=500, margin=dict(t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # --- 繪製 RSI 圖表 (如果開啟) ---
        if show_rsi:
            st.subheader("📉 強弱動能 (RSI)")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
            fig_rsi.update_layout(height=200, margin=dict(t=10, b=10))
            st.plotly_chart(fig_rsi, use_container_width=True)

        # --- 波動練習提示 ---
        st.divider()
        st.subheader("💡 練習觀測建議")
        volatility = (df['High'].iloc[-20:] - df['Low'].iloc[-20:]).mean()
        st.write(f"這檔股票近期的平均單日波動約為 **{volatility:.2f}** 元。")
        
        if curr_p > last_data['MA20']:
            st.success("目前股價站上月線 (20MA)，趨勢轉強，可以觀察是否能維持。")
        else:
            st.warning("目前股價在月線之下，屬於弱勢區間，新手請練習觀察底部訊號。")

        #--- 強弱勢股排行
        SCAN_LIST = ["2330.TW", "2317.TW", "2454.TW", "2308.TW", "2881.TW", "2882.TW", "2603.TW", "2609.TW", "2409.TW", "3481.TW"]
        st.subheader("🔥 過去一週市場戰況 (掃描儀)")
        if st.button("點擊刷新排行榜"):
            perf_df = get_performance_list()
            if not perf_df.empty:
                col_strong, col_weak = st.columns(2)
                with col_strong:
                    st.success("🚀 強勢股 (Top 5)")
                    st.table(perf_df.sort_values(by="漲跌幅", ascending=False).head(5))
                with col_weak:
                    st.error("📉 弱勢股 (Bottom 5)")
                    st.table(perf_df.sort_values(by="漲跌幅", ascending=True).head(5))
        st.divider()


        #---MACD
        if show_macd:
            st.subheader("📊 MACD 趨勢確認")
            
            # MACD 包含：Histogram (柱狀圖), MACD (快線), Signal (慢線)
            # 注意：pandas_ta 產出的欄位名稱通常為 MACD_12_26_9, MACDs_12_26_9, MACDh_12_26_9
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Bar(x=df.index, y=df['MACDh_12_26_9'], name='柱狀圖', 
                                    marker_color=['red' if x > 0 else 'green' for x in df['MACDh_12_26_9']]))
            fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_12_26_9'], name='DIF (快線)', line=dict(color='blue')))
            fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACDs_12_26_9'], name='MACD (慢線)', line=dict(color='orange')))
            fig_macd.update_layout(height=250, margin=dict(t=0, b=0))
            st.plotly_chart(fig_macd, use_container_width=True)

        # ---筆記區---
        st.write("---")
        st.subheader("📓 新手練習筆記 (Notion Style)")
        
        # 使用 session_state 儲存筆記內容，避免換股票時消失
        if 'my_note' not in st.session_state:
            st.session_state.my_note = "在此輸入你的觀察心得..."

        user_note = st.text_area("觀察隨筆", value=st.session_state.my_note, height=200)
        st.session_state.my_note = user_note # 更新 state
        st.download_button("💾 匯出筆記", user_note, file_name=f"stock_note_{datetime.now().strftime('%Y%m%d')}.txt")


        

except Exception as e:
    st.error(f"發生錯誤：{e}")
    st.info("提示：請檢查網路連線或股票代碼是否正確（台股需補上 .TW）。")