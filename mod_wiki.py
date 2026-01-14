import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 業務邏輯鎖定區 (V31.2.10)</p>', unsafe_allow_html=True)

    # 鎖定鍵狀態
    if 'wiki_locked' not in st.session_state: st.session_state.wiki_locked = True
    
    col_lock, _ = st.columns([1, 4])
    with col_lock:
        st.session_state.wiki_locked = st.toggle("🔒 規格鎖定鍵", value=st.session_state.wiki_locked)
        st.write(f"狀態: {'🔴 已鎖定 (ON)' if st.session_state.wiki_locked else '🟢 可討論 (OFF)'}")

    tab_crm, tab_code = st.tabs(["👥 夥伴管理規格", "💻 程式碼地圖"])

    with tab_crm:
        st.success("### 📂 夥伴管理 - 原子化欄位清單")
        st.markdown("""
        **1. 身份分類 (Mandatory)**
        - `type`: 必須區分 **Customer (客戶)** 與 **Supplier (供應商)**。
        
        **2. 公司基礎資料 (Atomic)**
        - `name`: 公司名稱 | `nationality`: 公司國籍
        - `tax_id`: 統一編號 | `address`: 公司地址
        - `main_phone`: 公司總機 | `main_email`: 公司通用電郵
        - `trade_items`: 交易項目 | `credit_limit`: 建議交易金額上限
        
        **3. 財務聯絡窗口 (Finance Contact)**
        - `fin_name`: 姓名 | `fin_email`: 專用電郵
        
        **4. 業務聯絡窗口 (Sales Contact)**
        - `sales_name`: 姓名 | `sales_email`: 專用電郵 | `sales_mobile`: 手機號碼
        """)
    
    with tab_code:
        try:
            with open("mod_crm.py", "r", encoding="utf-8") as f:
                st.code(f.read(), language="python")
        except: st.error("mod_crm.py 檔案讀取失敗")
