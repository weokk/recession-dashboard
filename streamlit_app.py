import streamlit as st
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go
from datetime import datetime

# 页面配置
st.set_page_config(page_title="非传统衰退指标看板", layout="wide")

st.title("📊 非传统经济衰退预警看板")
st.markdown("""
根据 *HuffPost* 报道，我们通过 **口红效应** (个人护理零售占比) 和 **男士内裤指标** (男装零售) 构建体感压力指数。
""")

# --- 环境变量处理 ---
# 优先从 Streamlit Secrets 读取，如果没有则报错
if "FRED_API_KEY" in st.secrets:
    api_key = st.secrets["FRED_API_KEY"]
else:
    st.error("未找到环境变量 'FRED_API_KEY'。请在 Streamlit Secrets 中配置。")
    st.stop()

# --- 侧边栏配置 ---
st.sidebar.header("时间范围")
current_year = datetime.now().year
# 年份滑块，范围从2000年到今年
start_year = st.sidebar.slider("选择起始年份", 2000, current_year, 2010)

# --- 数据获取函数 ---
@st.cache_data(ttl=86400) # 缓存数据24小时，避免频繁请求 API
def get_economic_data(api_key, start_date):
    try:
        fred = Fred(api_key=api_key)
        
        # 使用更稳健的季节性调整(SA)序列 ID
        # RETAILIRSA: 零售业：健康与个人护理商店 (口红效应代理)
        # RSMCL: 零售业：男装商店 (内裤指标代理)
        # UNRATE: 失业率
        # RETAILPMSA: 零售总额（不含机动车及零部件）
        
        series_map = {
            'Lipstick_Proxy': 'RETAILIRSA', 
            'Menswear_Proxy': 'RSMCL',
            'Total_Retail': 'RETAILPMSA',
            'Unemployment': 'UNRATE'
        }
        
        data_frames = {}
        for name, s_id in series_map.items():
            s = fred.get_series(s_id, observation_start=start_date)
            data_frames[name] = s
            
        df = pd.DataFrame(data_frames).ffill().dropna()
        return df
    except Exception as e:
        st.error(f"数据获取失败: {str(e)}")
        return None

# --- 执行逻辑 ---
start_dt = datetime(start_year, 1, 1)
data = get_economic_data(api_key, start_dt)

if data is not None:
    # 1. 计算口红指数 (占比)
    data['Lipstick_Index'] = (data['Lipstick_Proxy'] / data['Total_Retail']) * 100
    
    # 2. 归一化处理 (以便在同一个图表中对比波动趋势)
    data_norm = (data - data.min()) / (data.max() - data.min())

    # --- 仪表盘展示 ---
    c1, c2, c3 = st.columns(3)
    
    # 获取最新数据点
    latest = data.iloc[-1]
    prev = data.iloc[-2]
    
    # 逻辑判断
    is_lipstick_rising = latest['Lipstick_Index'] > prev['Lipstick_Index']
    is_menswear_falling = latest['Menswear_Proxy'] < prev['Menswear_Proxy']
    
    with c1:
        st.metric("最新失业率", f"{latest['Unemployment']}%", f"{latest['Unemployment'] - prev['Unemployment']:.2f}%", delta_color="inverse")
    with c2:
        lipstick_delta = "上升 (预警)" if is_lipstick_rising else "下降 (安全)"
        st.metric("口红效应强度", f"{latest['Lipstick_Index']:.2f}%", lipstick_delta, delta_color="normal" if is_lipstick_rising else "inverse")
    with c3:
        menswear_delta = "下滑 (预警)" if is_menswear_falling else "增长 (正常)"
        st.metric("男装消费趋势", f"${latest['Menswear_Proxy']:.0f}M", menswear_delta, delta_color="inverse" if is_menswear_falling else "normal")

    # --- 图表可视化 ---
    st.subheader("核心指标趋势图 (归一化对比)")
    st.caption("注：所有指标已归一化至 0-1 范围，以便观察同步波动。")
    
    fig = go.Figure()
    # 口红效应
    fig.add_trace(go.Scatter(x=data.index, y=data_norm['Lipstick_Index'], name="口红效应 (个人护理占比)", line=dict(color='#ff7f0e', width=3)))
    # 男装消费
    fig.add_trace(go.Scatter(x=data.index, y=data_norm['Menswear_Proxy'], name="男装需求 (内裤指标)", line=dict(color='#1f77b4', width=2)))
    # 失业率背景
    fig.add_trace(go.Scatter(x=data.index, y=data_norm['Unemployment'], name="失业率 (阴影区)", fill='tozeroy', line=dict(color='rgba(255, 0, 0, 0.2)'), opacity=0.3))
    
    fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- 深度分析 ---
    st.markdown("### 🛠 衰退逻辑分析")
    exp1 = st.expander("为什么看口红占比？")
    exp1.write("当口红占比（个人护理零售额占总零售额的比重）逆势上升时，说明消费者开始削减大额耐用品支出，转而通过低价奢侈品寻求补偿感。")
    
    exp2 = st.expander("为什么看男装消费？")
    exp2.write("男士服装（尤其是内裤）被认为是极度隐形的刚需。如果该项数值连续下滑，说明家庭预算已经紧缩到了必须推迟基本生活品更新的程度。")

    st.divider()
    st.dataframe(data.tail(12))