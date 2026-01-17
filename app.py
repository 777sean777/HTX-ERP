import streamlit as st
import core_engine

# --- 系統版本 ---
VERSION = "V2026.01.17-System-Ready" 
st.set_page_config(page_title=f"HTX ERP {VERSION}", layout="wide")

# --- 初始化核心 ---
core_engine.apply_custom_style()
supabase = core_engine.init_connection()

# --- 憲法第貳條：側邊欄 Dev Mode ---
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.write("HTX ERP System")
    
    st.markdown("---")
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
    "matrix": "📅 專案36個月預算",
    "so": "📝 銷售訂單 (SO)", 
    "po": "🛒 採購訂單 (PO)",
    "inventory": "📦 倉儲與庫存", # (雖然還沒實作，先留著位子)
    "finance": "📊 經營決策看板",
    "admin": "⚙️ 系統設定"  # <--- [NEW] 系統設定已掛載
}
choice_label = st.sidebar.radio("功能導航", list(menu.values()))

# 反查 Key
choice = [k for k, v in menu.items() if v == choice_label][0]

# --- 路由分發 ---
try:
    if choice == "home":
        st.title("🏠 財務任務中心 (Financial Task Center)")
        c1, c2 = st.columns(2)
        with c1:
            with st.container(border=True):
                st.subheader("📥 本月應開立發票 (AR)")
                st.caption("連動 SO 模組開發中...")
        with c2:
            with st.container(border=True):
                st.subheader("📤 本月應付帳款 (AP)")
                st.caption("連動 PO 模組開發中...")

    elif choice == "crm":
        import mod_crm
        mod_crm.show(supabase, "HTT")

    elif choice == "project":
        import mod_project_init
        mod_project_init.show(supabase)

    elif choice == "matrix":
        import mod_matrix
        mod_matrix.show(supabase)

    elif choice == "so":
        import mod_so
        mod_so.show(supabase)

    elif choice == "po":
        import mod_po
        mod_po.show(supabase)

    elif choice == "inventory":
        # import mod_inventory
        # mod_inventory.show(supabase)
        st.info("📦 倉儲模組建置中... (請先確認 Admin 設定)")

    elif choice == "finance":
        import mod_project_dashboard
        mod_project_dashboard.show(supabase)

    elif choice == "admin":  # <--- [NEW] Admin 模組路由
        import mod_admin
        mod_admin.show(supabase)

    else:
        st.warning(f"🚧 {choice_label} 模組建置中...")

except Exception as e:
    st.error("系統發生預期外錯誤")
    if st.session_state.dev_mode:
        st.exception(e)
