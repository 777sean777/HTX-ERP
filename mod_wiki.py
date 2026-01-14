import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 開發者地圖 (Code Wiki)</p>', unsafe_allow_html=True)
    st.write("點擊下方模組方塊，檢查業務邏輯與程式碼：")

    # --- 第一排模組 ---
    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.subheader("👥 夥伴管理")
            st.write("● **狀態:** 已上線 (V2.0)")
            if st.button("查看詳情", key="wiki_crm"):
                st.session_state.wiki_view = "CRM"

    with c2:
        with st.container(border=True):
            st.subheader("🚀 專案建檔")
            st.write("● **狀態:** 規劃中")
            if st.button("查看詳情", key="wiki_proj"):
                st.session_state.wiki_view = "PROJ"

    with c3:
        with st.container(border=True):
            st.subheader("📅 預算規劃")
            st.write("● **狀態:** 規劃中")
            if st.button("查看詳情", key="wiki_plan"):
                st.session_state.wiki_view = "PLAN"

    # --- 詳細內容展示區 ---
    view = st.session_state.get("wiki_view", "NONE")
    st.divider()

    if view == "CRM":
        st.success("### 📂 模組：合作夥伴管理 (CRM/SRM)")
        tab_logic, tab_code = st.tabs(["💡 業務邏輯框架", "💻 原始程式碼"])
        with tab_logic:
            st.write("""
            **1. 功能核心:** 建立公司所有往來客戶與供應商的身份證。
            **2. 風險控管:** 包含『建議交易金額上限』，用於後續採購/訂單警示。
            **3. 資料結構:** 包含統編、聯絡人、多組聯繫電話及地址。
            **4. 操作邏輯:** 支援一鍵測試填充、Upsert 存檔、清單搜尋、資料刪除。
            """)
        with tab_code:
            st.code(open("mod_crm.py", "r", encoding="utf-8").read(), language="python")

    elif view == "PROJ":
        st.warning("### 📂 模組：專案身分建檔")
        st.write("**業務框架:** 執行年度斷代，建立 Project ID。必須連動 CRM 中的客戶名稱。")
        st.info("程式碼編寫中...")

    elif view == "NONE":
        st.info("請點擊上方方塊查看模組細節。")
