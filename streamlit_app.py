import streamlit as st
import pandas as pd
import pandas_datareader as pdr
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(page_title="非传统衰退指标看板", layout="wide")

st.title("📊 非传统经济衰退预警看板")
st.markdown("""
根据 *HuffPost* 报道，我们通过 **口红效应** (化妆品零售) 和 **男士内裤指标** (男装零售) 
以及官方失业率构建了一个“体感压力指数”。
""")

# 侧边栏设置
st.sidebar.header("配置参数")
api_key = st.secrets["FRED_API_KEY"]
start_date = st.sidebar.date_input("开始日期", datetime(2018, 1, 1))

# 数据获取函数
def get_economic_data(api_key, start):
    # FRED 指标代码:
    # MRTSSM44612USS: 化妆品、美容用品零售额 (口红效应)
    # MRTSSM44811USS: 男装零售额 (内裤指标替代)
    # UNRATE: 官方失业率
    # RETAILIRSA: 零售总额 (用于归一化)
    series_ids = {
        'Lipstick_Proxy': 'MRTSSM44612USS',
        'Menswear_Proxy': 'MRTSSM44811USS',
        'Total_Retail': 'RETAILSMPCTSA',
        'Unemployment': 'UNRATE'
    }
    
    try:
        df = pdr.get_data_fred(list(series_ids.values()), start=start, api_key=api_key)
        df.columns = list(series_ids.keys())
        return df
    except Exception as e:
        st.error(f"数据获取失败: {e}")
        return None

if api_key:
    data = get_economic_data(api_key, start_date)
    
    if data is not None:
        # --- 逻辑构建 ---
        # 1. 口红指数：当化妆品增长超过零售总额增长时，数值上升
        data['Lipstick_Index'] = data['Lipstick_Proxy'] / data['Total_Retail']
        
        # 2. 衰退压力评分 (归一化计算)
        # 逻辑：口红指数上升 + 男装销量下降 + 失业率上升 = 高风险
        data['Stress_Score'] = (
            (data['Lipstick_Index'].pct_change() > 0).astype(int) + 
            (data['Menswear_Proxy'].pct_change() < 0).astype(int) + 
            (data['Unemployment'].diff() > 0).astype(int)
        )

        # 展示最新状态
        latest_score = data['Stress_Score'].iloc[-1]
        cols = st.columns(3)
        cols[0].metric("当前衰退压力评分 (0-3)", latest_score)
        cols[1].metric("口红效应强度", f"{data['Lipstick_Index'].iloc[-1]:.2f}")
        cols[2].metric("失业率", f"{data['Unemployment'].iloc[-1]}%")

        # --- 图表可视化 ---
        st.subheader("指标趋势分析")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Lipstick_Index'], name="口红指数 (相对热度)"))
        fig.add_trace(go.Scatter(x=data.index, y=data['Unemployment']/10, name="失业率 (缩放显示)", line=dict(dash='dash')))
        
        fig.update_layout(hovermode="x unified", title="口红效应 vs 失业率")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("原始数据概览")
        st.dataframe(data.tail(12))

        st.info("💡 逻辑解释：当蓝色线条（口红指数）在虚线（失业率）抬升前异常升高，通常意味着消费者开始转向低价替代品，预示衰退风险。")
else:
    st.warning("请在左侧侧边栏输入您的 FRED API Key 以加载实时数据。")