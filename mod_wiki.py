import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 開發者地圖 - 規格鎖定與全盤解析</p>', unsafe_allow_html=True)

    # 鎖定狀態指示器 (Session State)
    if 'wiki_locked' not in st.session_state: st.session_state.wiki_locked = True
    
    col_lock, col_info = st.columns([1, 4])
    with col_lock:
        lock_status = st.toggle("🔒 規格鎖定鍵", value=st.session_state.wiki_locked)
        st.session_state.wiki_locked = lock_status
        st.write(f"狀態: {'🔴 已鎖定 (ON)' if lock_status else '🟢 可討論 (OFF)'}")

    # 模組分區
    tabs = st.tabs(["👥 夥伴管理 (CRM/SRM)", "🚀 專案建檔", "📅 36個月規劃"])

    with tabs[0]:
        st.success("### 📂 夥伴管理模組 (CRM/SRM) - 細節全解析")
        t_logic, t_code = st.tabs(["💡 業務邏輯與連動", "💻 原始程式碼"])
        
        with t_logic:
            st.markdown("""
            #### 1. 身份分類 (Mandatory)
            - 必須區分 **[Customer]** 與 **[Supplier]**，這會影響後續訂單(SO)與採購(PO)的下拉清單。
            #### 2. 原子化聯絡網 (Atomic Contacts)
            - **[財務窗口]**: 姓名、專用電郵 (對帳用)。
            - **[業務窗口]**: 姓名、專用電郵、手機。
            #### 3. 風險控管
            - **[Credit Limit]**: 建議交易金額上限。連動至『採購錄入』時進行預警。
            #### 4. 連動關係
            - 此表為 `projects` 的父表 (Customer)。
            - 此表為 `transactions` 的關聯項 (Supplier/Customer)。
            """)
        with t_code:
            try:
                with open("mod_crm.py", "r", encoding="utf-8") as f:
                    st.code(f.read(), language="python")
            except: st.error("檔案讀取中...")
