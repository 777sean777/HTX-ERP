import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 業務邏輯鎖定區 (V31.2.09)</p>', unsafe_allow_html=True)
    
    if st.button("👥 夥伴管理 (CRM/SRM) 規格鎖定", use_container_width=True):
        st.session_state.focus_wiki = "CRM"

    focus = st.session_state.get("focus_wiki", "CRM")
    st.divider()

    if focus == "CRM":
        st.success("### 📂 夥伴管理模組 - 原子化欄位清單 (Locked)")
        st.markdown("""
        **1. 公司通訊 (一格一資訊)**
        - `company_email`: 公司通用電郵
        - `finance_email`: **財務專用電郵 (新增/鎖定)**
        - `company_phone`: 公司總機電話
        - `company_address`: 公司登記地址
        
        **2. 聯絡窗口 (一格一資訊)**
        - `contact_name`: 窗口姓名
        - `contact_mobile`: 窗口手機
        - `contact_email`: 窗口個人電郵
        """)
