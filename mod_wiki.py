import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 開發者地圖 - 業務邏輯鎖定區</p>', unsafe_allow_html=True)
    
    # 頂部導航方塊
    cols = st.columns(3)
    with cols[0]:
        if st.button("👥 夥伴管理 (CRM/SRM) 規格鎖定", use_container_width=True):
            st.session_state.focus_wiki = "CRM"

    focus = st.session_state.get("focus_wiki", "CRM")
    st.divider()

    if focus == "CRM":
        st.success("### 📂 夥伴管理模組 (CRM/SRM) - 鎖定規格書")
        t1, t2 = st.tabs(["🔒 業務規格與欄位 (不可私自更動)", "💻 程式碼實作"])
        
        with t1:
            st.markdown("""
            #### 1. 公司基本資訊 (Mandatory Fields)
            - **[ID]** 公司全稱 (Primary Key, 不可重複)
            - **[Tax ID]** 統一編號 (用於稅務開票)
            - **[Comp Mail]** 公司總機/財務電郵 (消失補回！鎖定！)
            - **[Address]** 公司登記/收貨地址
            #### 2. 風險控管核心 (Risk Logic)
            - **[Credit Limit]** 建議交易金額上限 (用於 PO 系統超額警示)
            #### 3. 聯絡窗口 (Contact Details)
            - **[Person]** 主要窗口姓名 | **[Title]** 職稱
            - **[Mobile]** 手機號碼 | **[Personal Mail]** 窗口電郵 (鎖定！)
            #### 4. 交易細節
            - **[Items]** 交易項目 | **[Remarks]** 備註備忘錄
            """)
            st.error("⚠️ 以上規格已鎖定。若 AI 產出代碼缺失欄位，請視為系統故障並要求重寫。")
        
        with t2:
            with open("mod_crm.py", "r", encoding="utf-8") as f:
                st.code(f.read(), language="python")
