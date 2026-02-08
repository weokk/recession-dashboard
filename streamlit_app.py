import streamlit as st
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
from datetime import datetime

# 页面配置
st.set_page_config(page_title="经济衰退非传统指标", layout="wide")

st.title("📊 非传统经济衰退预警看板 (V2.0)")
st.markdown("同步监控：**口红效应**（红色）、**男装指标**（蓝色）与**官方衰退期**（阴影）。")

# --- 环境变量 ---
if "FRED_API_KEY" in st.secrets:
    api_key = st.secrets["FRED_API_KEY"]
else:
    st.error("请先在 Streamlit Secrets 中设置 FRED_API_KEY")
    st.stop()

# --- 侧边栏 ---
start_year = st.sidebar.slider("起始年份", 2000, 2025, 2008)

@st.cache_data(ttl=86400)
def get_pro_data(api_key, start_date):
    fred = Fred(api_key=api_key)
    # 使用目前最稳定的 ID
    series_map = {
        'Unemployment': 'UNRATE',           # 失业率
        'Lipstick_Proxy': 'MRTSSM44611USS', # 药妆零售
        'Menswear_Proxy': 'MRTSSM44811USS', # 男装零售 (已更换为稳定版)
        'Total_Retail': 'RSXFS',            # 零售总计
        'Recession': 'USREC'                # 官方衰退期 (1代表衰退中)
    }
    
    df_map = {}
    for name, s_id in series_map.items():
        try:
            df_map[name] = fred.get_series(s_id, observation_start=start_date)
        except:
            st.sidebar.warning(f"无法加载 {name}")
            
    df = pd.DataFrame(df_map).ffill().dropna()
    return df

# --- 执行 ---
data = get_pro_data(api_key, datetime(start_year, 1, 1))

if data is not None:
    # 指标计算
    data['Lipstick_Index'] = (data['Lipstick_Proxy'] / data['Total_Retail']) * 100
    
    # 归一化处理 (避开单一点的干扰)
    def normalize(s):
        return (s - s.min()) / (s.max() - s.min())

    # --- 绘图 ---
    fig = go.Figure()

    # 1. 绘制官方衰退阴影 (历史背景)
    recession_periods = data[data['Recession'] == 1]
    if not recession_periods.empty:
        fig.add_trace(go.Scatter(
            x=data.index, y=data['Recession'],
            fill='tozeroy', mode='none',
            fillcolor='rgba(255, 0, 0, 0.1)',
            name='NBER 官方衰退期'
        ))

    # 2. 口红效应 (占比趋势)
    fig.add_trace(go.Scatter(
        x=data.index, y=normalize(data['Lipstick_Index']),
        name="口红效应 (占比趋势)",
        line=dict(color='#FF4B4B', width=3)
    ))

    # 3. 男装需求 (内裤指标)
    if 'Menswear_Proxy' in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index, y=normalize(data['Menswear_Proxy']),
            name="男装需求 (内裤指标)",
            line=dict(color='#0068C9', width=2, dash='dot')
        ))

    # 4. 失业率 (作为对比)
    fig.add_trace(go.Scatter(
        x=data.index, y=normalize(data['Unemployment']),
        name="失业率趋势",
        line=dict(color='rgba(255, 255, 255, 0.4)', width=1)
    ))

    fig.update_layout(
        template="plotly_dark",
        height=600,
        hovermode="x unified",
        title=f"{start_year} 年以来的历史指标联动 (已归一化)",
        yaxis=dict(title="压力指数 (0-1)"),
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 预警逻辑说明 ---
    st.subheader("💡 如何阅读此图？")
    cols = st.columns(2)
    with cols[0]:
        st.write("**历史经验：**")
        st.write("- 在 2008 年衰退前，口红占比（红线）出现了显著的平台期抬升。")
        st.write("- 在 2020 年衰退时，所有指标瞬间崩塌。")
    with cols[1]:
        st.write("**当前状况：**")
        latest_val = data['Lipstick_Index'].iloc[-1]
        avg_val = data['Lipstick_Index'].rolling(12).mean().iloc[-1]
        if latest_val > avg_val:
            st.warning(f"⚠️ 预警：当前口红占比 ({latest_val:.2f}%) 高于 12 个月均值 ({avg_val:.2f}%)，符合新闻中的衰退逻辑。")
        else:
            st.success("✅ 正常：口红占比目前处于相对平稳区间。")

    with st.expander("原始数据对齐表"):
        st.dataframe(data.tail(12))