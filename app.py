import streamlit as st
import core_engine

VERSION = "V2026.01.14-06" 

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
    "📑 實際訂單/採購錄入", 
    "📊 經營決策看板"
]
choice = st.sidebar.radio("功能選單", menu)

# --- 功能分流 (加入錯誤捕捉，避免檔案缺失導致當機) ---
try:
    if choice == "🛡️ 系統 Wiki (開發地圖)":
        import mod_wiki
        mod_wiki.show()
    elif choice == "👥 合作夥伴管理":
        import mod_crm
        mod_crm.show(supabase, dept)
    elif choice == "🚀 專案身分建檔":
        st.info("🏗️ 專案身分建檔開發中，請先在 Wiki 查看邏輯。")
    else:
        st.markdown(f'<p class="main-header">{choice}</p>', unsafe_allow_html=True)
        st.write("### 🏗️ 模組建置中...")
except Exception as e:
    st.error(f"🚨 模組加載失敗：請確認 GitHub 檔案是否存在。")
    st.exception(e)
