import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 開發者地圖 (Code Wiki)</p>', unsafe_allow_html=True)
    st.write("點擊下方模組方塊，檢查業務邏輯與程式碼：")

    # --- 第一排模組方塊 ---
    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.subheader("👥 夥伴管理")
            st.write("● **狀態:** 已上線 (V2.0)")
            st.write("● **功能:** CRM / 風險控管")
            if st.button("查看邏輯與代碼", key="wiki_crm"):
                st.session_state.wiki_view = "CRM"

    with c2:
        with st.container(border=True):
            st.subheader("🚀 專案建檔")
            st.write("● **狀態:** 規劃中")
            st.write("● **功能:** 年度斷代 / ID 生成")
            if st.button("查看邏輯與代碼", key="wiki_proj"):
                st.session_state.wiki_view = "PROJ"

    with c3:
        with st.container(border=True):
            st.subheader("📅 預算規劃")
            st.write("● **狀態:** 規劃中")
            st.write("● **功能:** 36個月矩陣規劃")
            if st.button("查看邏輯與代碼", key="wiki_plan"):
                st.session_state.wiki_view = "PLAN"

    # --- 詳細內容展示區 ---
    view = st.session_state.get("wiki_view", "NONE")
    st.divider()

    if view == "CRM":
        st.success("### 📂 模組：合作夥伴管理 (CRM/SRM)")
        tab_logic, tab_code = st.tabs(["💡 業務邏輯框架", "💻 原始程式碼"])
        with tab_logic:
            st.markdown("""
            #### 1. 功能核心
            建立並維護與客戶及供應商的往來資料，作為所有交易的底層索引。
            #### 2. 風險控管 (Risk Management)
            * **建議交易金額上限**: 這是本系統的核心警示基準。
            * **邏輯**: 在後續訂單與採購錄入時，若單筆金額超過此設定，系統必須彈出黃色警告。
            #### 3. 欄位定義
            * 包含基本通訊、統編、以及專屬聯絡窗口資訊。
            #### 4. 自動化工具
            * 支援 `Antigravity` 一鍵填充測試數據。
            """)
        with tab_code:
            try:
                with open("mod_crm.py", "r", encoding="utf-8") as f:
                    st.code(f.read(), language="python")
            except:
                st.error("無法讀取 mod_crm.py，請確認檔案已上傳至 GitHub。")

    elif view == "PROJ":
        st.warning("### 📂 模組：專案身分建檔")
        st.write("**業務框架:** 執行年度斷代，建立 Project ID。必須連動 CRM 中的客戶名稱。")
        st.info("程式碼編寫中...")

    elif view == "NONE":
        st.info("請點擊上方方塊查看模組細節。")
