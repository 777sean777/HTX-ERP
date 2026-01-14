import streamlit as st
import core_engine

# --- 系統版本 ---
VERSION = "V2026.01.14-Build02" # 更新版本號
st.set_page_config(page_title=f"HTX ERP {VERSION}", layout="wide")

# --- 初始化核心 ---
core_engine.apply_custom_style()
supabase = core_engine.init_connection()

# --- 憲法第貳條：側邊欄 Dev Mode ---
with st.sidebar:
    try:
        # 如果你有 logo.png 可以放，沒有會自動忽略
        st.image("logo.png", use_container_width=True)
    except:
        st.write("HTX ERP System")
    
    st.markdown("---")
    # Master Switch
    if 'dev_mode' not in st.session_state: st.session_state.dev_mode = False
    st.session_state.dev_mode = st.toggle("🛠️ 開發者模式 (Dev Mode)", value=st.session_state.dev_mode)
    
    if st.session_state.dev_mode:
        st.caption("🔴 測試功能已啟用")
    
    st.markdown("---")

# --- 功能導航 ---
menu = {
    "home": "🏠 財務任務中心 (首頁)",
    "crm": "👥 合作夥伴管理",
    "project": "🚀 專案身分建檔",
    "matrix": "📅 專案36個月預算", # 這一頁現在生效了
    "inventory": "📦 倉儲與庫存",
    "finance": "📊 經營決策看板"
}
choice_label = st.sidebar.radio("功能導航", list(menu.values()))

# 反查 Key
choice = [k for k, v in menu.items() if v == choice_label][0]

# --- 路由分發 ---
try:
    if choice == "home":
        # 憲法第壹條：首頁即看板
        st.title("🏠 財務任務中心 (Financial Task Center)")
        st.info("🚧 系統初始化中... 待 SO/PO 模組建立後，此處將自動掃描待辦款項。")
        
        # 預留看板空位
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.subheader("📥 本月應開立發票 (AR)")
                st.caption("尚無待辦事項 (需連接 SO 模組)")
        with c2:
            with st.container(border=True):
                st.subheader("📤 本月應付帳款 (AP)")
                st.caption("尚無待辦事項 (需連接 PO 模組)")

    elif choice == "crm":
        import mod_crm
        mod_crm.show(supabase, "HTT") # 暫時預設部門

    elif choice == "project":
        import mod_project_init
        mod_project_init.show(supabase)

    elif choice == "matrix":
        # 🟢 這裡解開了！連接 mod_matrix.py
        import mod_matrix
        mod_matrix.show(supabase)

    else:
        st.warning(f"🚧 {choice_label} 模組建置中，請依照 Wiki 憲法進度開發。")

except Exception as e:
    st.error("系統發生預期外錯誤")
    if st.session_state.dev_mode:
        st.exception(e)
