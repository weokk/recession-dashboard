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
1. **口红效应**：个人护理零售额占总零售比例。
2. **男士内裤指标**：男装零售趋势。
""")

# --- 环境变量处理 ---
if "FRED_API_KEY" in st.secrets:
    api_key = st.secrets["FRED_API_KEY"]
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
    
    # 重新优化的 Series ID 映射表
    series_map = {
        'Unemployment': 'UNRATE',                  # 失业率
        'Lipstick_Proxy': 'MRTSSM44611USS',        # 药妆零售 (Health and Personal Care)
        'Menswear_Proxy': 'RETAILMCL',             # 男装商店零售 (更稳健的 ID)
        'Total_Retail': 'RSXFS'                    # 零售总额
    }
    
    combined_data = pd.DataFrame()
    
    for name, s_id in series_map.items():
        try:
            s = fred.get_series(s_id, observation_start=start_date)
            # 确保索引对齐
            combined_data[name] = s
        except Exception as e:
            st.warning(f"无法加载指标 {name} (ID: {s_id})。逻辑将跳过此指标。")
            
    if combined_data.empty:
        return None
        
    return combined_data.ffill().dropna()

# --- 执行逻辑 ---
start_dt = datetime(start_year, 1, 1)
data = get_economic_data(api_key, start_dt)

if data is not None and not data.empty:
    # 动态检查哪些列可用
    cols = data.columns.tolist()
    
    # 1. 计算口红指数 (如果相关列都存在)
    if 'Lipstick_Proxy' in cols and 'Total_Retail' in cols:
        data['Lipstick_Index'] = (data['Lipstick_Proxy'] / data['Total_Retail']) * 100
    
    # 2. 归一化处理（用于图表对比波动）
    data_norm = (data - data.min()) / (data.max() - data.min())

    # --- 仪表盘展示 ---
    st.subheader("🚩 核心预警状态")
    metrics_cols = st.columns(len(cols))
    
    latest = data.iloc[-1]
    prev = data.iloc[-2]
    
    # 动态渲染 Metric 卡片
    for i, col in enumerate(cols):
        with metrics_cols[i]:
            val = latest[col]
            diff = val - prev[col]
            if col == 'Unemployment':
                st.metric("失业率", f"{val}%", f"{diff:.2f}%", delta_color="inverse")
            elif col == 'Lipstick_Proxy':
                st.metric("个人护理(M$)", f"{val:,.0f}", f"{diff:,.0f}")
            elif col == 'Menswear_Proxy':
                st.metric("男装零售(M$)", f"{val:,.0f}", f"{diff:,.0f}", delta_color="normal" if diff > 0 else "inverse")
            elif col == 'Total_Retail':
                st.metric("零售总计(M$)", f"{val:,.0f}", f"{diff:,.0f}")

    # --- 图表可视化 ---
    st.subheader("📈 趋势对比 (归一化)")
    fig = go.Figure()
    
    if 'Lipstick_Index' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data_norm['Lipstick_Index'], name="口红效应 (化妆品占比)", line=dict(color='#FF4B4B', width=3)))
    
    if 'Menswear_Proxy' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data_norm['Menswear_Proxy'], name="男装需求", line=dict(color='#0068C9', width=2)))
    
    if 'Unemployment' in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data_norm['Unemployment'], name="失业率 (基准)", fill='tozeroy', line=dict(color='rgba(128, 128, 128, 0.2)')))
    
    fig.update_layout(template="plotly_dark", hovermode="x unified", height=500, margin=dict(t=30, b=30))
    st.plotly_chart(fig, use_container_width=True)

    # --- 逻辑分析 ---
    st.info("💡 **观察提示**：当红色线条（口红占比）在失业率显著上升之前出现异常的尖峰，通常是经济衰退的先行信号。")
    
    with st.expander("查看数据底表"):
        st.dataframe(data.tail(20))
else:
    st.error("无法加载任何数据，请检查 API Key 或网络。")