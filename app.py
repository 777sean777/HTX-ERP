import streamlit as st
import core_engine

# --- 版本定義 (每次更新程式碼請修改此處) ---
VERSION = "V2026.01.14-01" 

st.set_page_config(page_title=f"HTX ERP {VERSION}", layout="wide")
core_engine.apply_custom_style()
supabase = core_engine.init_connection()

# --- 側邊欄：顯示 Logo 與 版本 ---
try:
    st.sidebar.image("logo.png", use_container_width=True)
except:
    st.sidebar.warning("⚠️ logo.png 未找到")

st.sidebar.markdown(f"**系統版本:** `{VERSION}`")
dept = core_engine.get_dept()

st.sidebar.divider()
menu = ["📊 經營決策看板", "📅 預算與現金流規劃", "📑 採購與訂單(實際)", "🛡️ 系統 Wiki"]
choice = st.sidebar.radio("功能選單", menu)

# --- 功能分流 ---
if choice == "🛡️ 系統 Wiki":
    import mod_wiki
    mod_wiki.show()
elif choice == "📅 預算與現金流規劃":
    st.markdown(f'<p class="main-header">📅 {dept} 預算與現金流規劃</p>', unsafe_allow_html=True)
    st.info("現金估算表模組開發中...")
else:
    st.markdown(f'<p class="main-header">{choice}</p>', unsafe_allow_html=True)
    st.write("模組建置中...")
