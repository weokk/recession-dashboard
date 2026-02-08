import streamlit as st
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
from datetime import datetime

# 页面配置
st.set_page_config(page_title="非传统衰退指标看板", layout="wide")

st.title("📊 非传统经济衰退预警看板")
st.markdown("""
根据 *HuffPost* 报道，我们通过监控以下指标来观察经济健康度：
1. **口红效应**：个人护理零售额占总零售比例（经济压力大时人们更倾向于买小件奢侈品）。
2. **男士内裤指标**：男装零售趋势（家庭削减开支的首选，因其极度隐蔽）。
""")

# --- 环境变量处理 ---
if "FRED_API_KEY" in st.secrets:
    api_key = st.secrets["FRED_API_KEY"]
elif "FRED_API_KEY" in st.sidebar.text_input("手动输入 API Key (仅用于临时测试)", type="password"):
    api_key = st.sidebar.text_input("手动输入 API Key (仅用于临时测试)", type="password")
else:
    st.error("未找到环境变量 'FRED_API_KEY'。请在 Streamlit Secrets 中配置。")
    st.stop()

# --- 侧边栏配置 ---
st.sidebar.header("时间范围")
current_year = datetime.now().year
start_year = st.sidebar.slider("选择起始年份", 2000, current_year, 2010)

# --- 数据获取函数 ---
@st.cache_data(ttl=86400)
def get_economic_data(api_key, start_date):
    fred = Fred(api_key=api_key)
    
    # 重新选定的、在 FRED 上最稳定的 Series ID
    # UNRATE: 失业率
    # MRTSSM44611USS: 零售额：健康与个人护理商店 (Health and Personal Care Stores)
    # MRTSSM448111USS: 零售额：男装商店 (Men's Clothing Stores)
    # RSXFS: 零售和食品服务总额（不含机动车及零部件）- 常用基准
    
    series_map = {
        'Unemployment': 'UNRATE',
        'Lipstick_Proxy': 'MRTSSM44611USS', 
        'Menswear_Proxy': 'MRTSSM448111USS',
        'Total_Retail': 'RSXFS'
    }
    
    combined_data = pd.DataFrame()
    
    for name, s_id in series_map.items():
        try:
            s = fred.get_series(s_id, observation_start=start_date)
            combined_data[name] = s
        except Exception as e:
            st.warning(f"无法加载指标 {name} (ID: {s_id}): {e}")
            
    if combined_data.empty:
        return None
        
    return combined_data.ffill().dropna()

# --- 执行逻辑 ---
start_dt = datetime(start_year, 1, 1)
data = get_economic_data(api_key, start_dt)

if data is not None and not data.empty:
    # 检查必要列是否存在
    required_cols = ['Lipstick_Proxy', 'Total_Retail', 'Menswear_Proxy', 'Unemployment']
    available_cols = data.columns.tolist()
    
    if all(col in available_cols for col in required_cols):
        # 1. 计算口红指数 (占比)
        data['Lipstick_Index'] = (data['Lipstick_Proxy'] / data['Total_Retail']) * 100
        
        # 2. 归一化处理（用于图表对比）
        data_norm = (data - data.min()) / (data.max() - data.min())

        # --- 仪表盘展示 ---
        st.subheader("🚩 核心预警状态")
        c1, c2, c3 = st.columns(3)
        
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        with c1:
            diff = latest['Unemployment'] - prev['Unemployment']
            st.metric("失业率", f"{latest['Unemployment']}%", f"{diff:.2f}%", delta_color="inverse")
        with c2:
            is_up = latest['Lipstick_Index'] > prev['Lipstick_Index']
            st.metric("口红效应强度", f"{latest['Lipstick_Index']:.2f}%", "上升 (预警)" if is_up else "下降", delta_color="normal" if is_up else "inverse")
        with c3:
            is_down = latest['Menswear_Proxy'] < prev['Menswear_Proxy']
            st.metric("男装消费额", f"${latest['Menswear_Proxy']:,.0f}M", "下滑 (预警)" if is_down else "正常", delta_color="inverse" if is_down else "normal")

        # --- 图表可视化 ---
        st.subheader("📈 趋势对比 (归一化)")
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(x=data.index, y=data_norm['Lipstick_Index'], name="口红效应 (化妆品占比)", line=dict(color='#FF4B4B', width=3)))
        fig.add_trace(go.Scatter(x=data.index, y=data_norm['Menswear_Proxy'], name="男装需求 (内裤指标)", line=dict(color='#0068C9', width=2)))
        fig.add_trace(go.Scatter(x=data.index, y=data_norm['Unemployment'], name="失业率 (基准线)", fill='tozeroy', line=dict(color='rgba(128, 128, 128, 0.2)')))
        
        fig.update_layout(template="plotly_dark", hovermode="x unified", height=500)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("查看底层数据"):
            st.dataframe(data.tail(20))
    else:
        st.error(f"下载的数据不完整。获取到的列有: {available_cols}。请检查 API Key 权限或稍后再试。")
else:
    st.info("正在等待数据加载... 请确保您的 API Key 有效。")