import streamlit as st
import core_engine

VERSION = "V2026.01.14-04" 

st.set_page_config(page_title=f"HTX ERP {VERSION}", layout="wide")
core_engine.apply_custom_style()
supabase = core_engine.init_connection()

# --- 側邊欄 ---
try:
    st.sidebar.image("logo.png", use_container_width=True)
except:
    st.sidebar.warning("⚠️ logo.png 未找到")

st.sidebar.markdown(f"**系統版本:** `{VERSION}`")
dept = core_engine.get_dept()

st.sidebar.divider()
# 依照你的經營邏輯重新排列菜單
menu = [
    "🚀 專案身分建檔", 
    "📅 36個月細節規劃", 
    "📑 實際訂單/採購錄入", 
    "📊 經營決策看板", 
    "👥 合作夥伴管理", 
    "🛡️ 系統 Wiki"
]
choice = st.sidebar.radio("功能選單", menu)

# --- 功能分流 ---
if choice == "🛡️ 系統 Wiki":
    import mod_wiki
    mod_wiki.show()
elif choice == "🚀 專案身分建檔":
    import mod_project_init
    mod_project_init.show(supabase, dept)
elif choice == "👥 合作夥伴管理":
    import mod_crm
    mod_crm.show(supabase, dept)
else:
    st.markdown(f'<p class="main-header">{choice}</p>', unsafe_allow_html=True)
    st.info(f"🏗️ {choice} 模組升級中，請先完成前置資料建檔。")
