import streamlit as st
import core_engine

# 初始化設置
st.set_page_config(page_title="HTX ERP V31.2 Pro", layout="wide")
core_engine.apply_custom_style()
supabase = core_engine.init_connection()

# 側邊導航
st.sidebar.image("https://www.your-logo-url.com/logo.png", width=200) # 這裡你可以換成你的Logo
dept = core_engine.get_dept()

st.sidebar.divider()
menu = ["📊 經營決策看板", "📅 預算與現金流規劃", "📑 採購與訂單(實際)", "👥 合作夥伴管理", "🛡️ 系統 Wiki"]
choice = st.sidebar.radio("功能選單", menu)

# 分流邏輯
if choice == "🛡️ 系統 Wiki":
    st.markdown('<p class="main-header">🛡️ 系統記憶大腦 & 開發者地圖</p>', unsafe_allow_html=True)
    st.info(f"當前操作環境：{dept}")
    # 這裡未來會載入 mod_wiki.py
    
elif choice == "📅 預算與現金流規劃":
    st.markdown(f'<p class="main-header">📅 {dept} 預算與現金流規劃</p>', unsafe_allow_html=True)
    # 這裡未來會載入按你那張截圖格式設計的輸入頁面
    
else:
    st.write(f"### {choice} 模組開發中...")
    st.image("https://via.placeholder.com/800x400.png?text=Module+Under+Construction")
