import streamlit as st
import core_engine

# --- 版本定義 ---
VERSION = "V2026.01.14-07" 

st.set_page_config(page_title=f"HTX ERP {VERSION}", layout="wide")
core_engine.apply_custom_style()
supabase = core_engine.init_connection()

# --- 側邊欄 ---
try:
    st.sidebar.image("logo.png", use_container_width=True)
except:
    pass

st.sidebar.markdown(f"**系統版本:** `{VERSION}`")
dept = core_engine.get_dept()

st.sidebar.divider()
menu = [
    "🛡️ 系統 Wiki (開發地圖)", 
    "👥 合作夥伴管理",
    "🚀 專案身分建檔", 
    "📅 36個月細節規劃", 
    "📑 實際訂單/採購錄入"
]
choice = st.sidebar.radio("功能選單", menu)

# --- 路由與異常處理 ---
try:
    if choice == "🛡️ 系統 Wiki (開發地圖)":
        import mod_wiki
        mod_wiki.show()
    elif choice == "👥 合作夥伴管理":
        import mod_crm
        mod_crm.show(supabase, dept)
    else:
        st.markdown(f'<p class="main-header">{choice}</p>', unsafe_allow_html=True)
        st.info("🏗️ 模組開發中，請先參考 Wiki 地圖。")
except Exception as e:
    st.error("🚨 模組運行錯誤")
    st.exception(e)
