# recession-dashboard这是一个为你的 GitHub 仓库准备的专业 `README.md` 模板。它包含了项目背景、核心逻辑、技术实现以及部署指南。

---

# 📊 非传统经济衰退预警看板 (Unconventional Recession Dashboard)

这是一个基于 Streamlit 构建的实时数据可视化应用，旨在通过“非传统经济指标”监测体感经济压力。

本项目灵感来源于 [HuffPost 的报道](https://www.huffpost.com/entry/recession-indicators-sex-work-hair-hems-goog_l_697b75dde4b055d1873692d2)，探索官方失业率数据之外的“生活化”经济预警信号。

## 💡 核心逻辑：为什么关注这些指标？

传统的宏观经济指标（如 GDP）通常具有滞后性。本项目选取了两个极具代表性的非传统指标：

1.  **口红效应 (Lipstick Effect)**：
    *   **逻辑**：在经济动荡时期，消费者会放弃购买大额奢侈品（如名表、豪车），转而购买小额的“安慰性”消费品（如口红、高端个人护理）。
    *   **数据表达**：个人护理店零售额占整体零售总额的比例。
2.  **男士内裤指标 (Menswear/Underwear Index)**：
    *   **逻辑**：前联储主席格林斯潘曾指出，男士内裤是极度隐形的刚需。当家庭预算严重紧缩时，男士会优先推迟更换看不见的内裤。
    *   **数据表达**：男士服装店零售总额的波动。
3.  **先行性判断**：当**口红占比上升**且**男装需求下滑**时，通常预示着消费者信心已触底，衰退压力增大。

## 🚀 功能特性

*   **实时数据接入**：通过 St. Louis FRED API 获取最新美国经济数据。
*   **归一化对比**：将失业率、零售占比、服装消费等不同量纲的数据统一缩放，直观观察同步波动。
*   **官方衰退阴影区**：自动标出 NBER 认定的历史衰退期，验证指标的先行预警能力。
*   **动态预警系统**：自动计算当前数据与过去 12 个月均值的偏移，给出风险提示。

## 🛠️ 技术栈

*   **Python 3.9+**
*   **Streamlit**: 用于构建交互式 Web 界面。
*   **FredAPI**: 圣路易斯联邦储备银行数据接口。
*   **Plotly**: 交互式动态图表库。
*   **Pandas**: 数据清洗与指标计算。

## 📋 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 获取 FRED API Key
访问 [FRED API 官网](https://fred.stlouisfed.org/docs/api/api_key.html) 免费申请一个 API Key。

### 4. 本地运行
在项目根目录创建 `.streamlit/secrets.toml` 文件：
```toml
FRED_API_KEY = "你的_API_KEY"
```
运行应用：
```bash
streamlit run streamlit_app.py
```

## 🌐 部署到 Streamlit Cloud

1. 将代码推送到 GitHub 仓库。
2. 登录 [Streamlit Cloud](https://share.streamlit.io/) 并连接此仓库。
3. 在 App 设置中找到 **Secrets**，添加以下环境变量：
   ```toml
   FRED_API_KEY = "你的_API_KEY"
   ```
4. 点击部署，大功告成！

## 📊 数据源说明
*   **失业率**: `UNRATE`
*   **个人护理零售**: `MRTSSM44611USS`
*   **男士服装零售**: `MRTSSM44811USS`
*   **零售总计**: `RSXFS`
*   **官方衰退期**: `USREC`

---

### 免责声明
本工具仅用于学术研究和兴趣探索，不构成任何投资建议。经济预测具有高度不确定性，请结合多种官方指标进行综合分析。