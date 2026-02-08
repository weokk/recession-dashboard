import streamlit as st
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
from datetime import datetime

# 页面配置
st.set_page_config(page_title="非传统衰退指标看板", layout="wide")

st.title("📊 非传统经济衰退预警看板")
st.markdown("""
根据 *HuffPost* 报道，我们通过 **口红效应** (化妆品零售) 和 **男士内裤指标** (男装零售) 构建体感压力指数。
数据来源：St. Louis FRED。
""")

# 侧边栏
st.sidebar.header("配置参数")
api_key = st.secrets["FRED_API_KEY"]
start_year = st.sidebar.slider("选择起始年份", 2000, 2024, 2015)

# 数据获取逻辑
def get_data(api_key, start_date):
    try:
        fred = Fred(api_key=api_key)
        # MRTSSM44612USS: 化妆品、美容用品零售额
        # MRTSSM44811USS: 男装零售额
        # UNRATE: 失业率
        # RSXFS: 零售和食品服务总额 (用于对比)
        
        series = {
            'Lipstick_Proxy': 'MRTSSM44612USS',
            'Menswear_Proxy': 'MRTSSM44811USS',
            'Total_Retail': 'RSXFS',
            'Unemployment': 'UNRATE'
        }
        
        df_list = []
        for name, s_id in series.items():
            s = fred.get_series(s_id, observation_start=start_date)
            df_list.append(pd.DataFrame({name: s}))
            
        df = pd.concat(df_list, axis=1).ffill().dropna()
        return df
    except Exception as e:
        st.error(f"获取数据时出错: {e}")
        return None

if api_key:
    start_dt = datetime(start_year, 1, 1)
    data = get_data(api_key, start_dt)
    
    if data is not None:
        # --- 计算指标 ---
        # 口红效应指数：化妆品增速 vs 整体零售增速
        data['Lipstick_Index'] = (data['Lipstick_Proxy'] / data['Total_Retail']) * 100
        
        # 归一化处理以便对比
        data_norm = (data - data.min()) / (data.max() - data.min())
        
        # 核心指标卡
        c1, c2, c3 = st.columns(3)
        current_unemployment = data['Unemployment'].iloc[-1]
        last_unemployment = data['Unemployment'].iloc[-2]
        
        c1.metric("当前失业率", f"{current_unemployment}%", f"{current_unemployment-last_unemployment:.1f}%")
        
        # 逻辑判断：如果化妆品比例上升且男装下降
        is_lipstick_up = data['Lipstick_Index'].diff().iloc[-1] > 0
        c2.metric("口红效应倾向", "增强" if is_lipstick_up else "减弱")
        
        # --- 绘图 ---
        st.subheader("趋势对比图 (归一化)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data_norm['Lipstick_Index'], name="口红效应 (化妆品占比)"))
        fig.add_trace(go.Scatter(x=data.index, y=data_norm['Menswear_Proxy'], name="男装需求 (内裤指标)"))
        fig.add_trace(go.Scatter(x=data.index, y=data_norm['Unemployment'], name="失业率", line=dict(dash='dot', color='red')))
        
        fig.update_layout(template="plotly_dark", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("🔍 **数据解读：**")
        st.write("1. 当红色虚线(失业率)上升前，蓝色线(口红效应)往往会率先出现剧烈波动。")
        st.write("2. 橙色线(男装)的持续低迷通常预示着家庭可支配收入的紧缩。")
        
        with st.expander("查看原始数据"):
            st.dataframe(data.tail(20))
else:
    st.info("💡 请在侧边栏输入 FRED API Key。你可以从 [FRED 官网](https://fred.stlouisfed.org/docs/api/api_key.html) 免费申请。")