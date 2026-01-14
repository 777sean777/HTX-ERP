import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 系統開發地圖</p>', unsafe_allow_html=True)
    
    # --- 頂部模組方塊 ---
    cols = st.columns(3)
    
    with cols[0]:
        with st.container(border=True):
            st.subheader("👥 夥伴管理")
            st.caption("檔案: mod_crm.py")
            if st.button("檢視邏輯與代碼", key="view_crm"):
                st.session_state.wiki_focus = "CRM"

    with cols[1]:
        with st.container(border=True):
            st.subheader("🚀 專案建檔")
            st.caption("檔案: mod_project.py")
            if st.button("檢視邏輯與代碼", key="view_proj"):
                st.session_state.wiki_focus = "PROJ"

    with cols[2]:
        with st.container(border=True):
            st.subheader("📅 預算規劃")
            st.caption("檔案: mod_plan.py")
            if st.button("檢視邏輯與代碼", key="view_plan"):
                st.session_state.wiki_focus = "PLAN"

    # --- 詳細內容區 ---
    focus = st.session_state.get("wiki_focus", "")
    st.divider()

    if focus == "CRM":
        st.success("### 📁 模組詳情：合作夥伴管理")
        t1, t2 = st.tabs(["💡 業務邏輯框架", "💻 原始原始碼"])
        with t1:
            st.markdown("""
            **1. 功能核心**: 集中管理客戶(Customer)與供應商(Supplier)。
            **2. 風險控管**: 設定 Credit Limit (交易上限)，用於採購警示。
            **3. 操作邏輯**: 支援一鍵測試填充、自動抓取舊資料進行修改、防止重複建檔。
            """)
        with t2:
            try:
                with open("mod_crm.py", "r", encoding="utf-8") as f:
                    st.code(f.read(), language="python")
            except:
                st.error("讀取檔案失敗，請確認 mod_crm.py 已上傳。")
    elif focus == "PROJ":
        st.warning("### 📁 模組詳情：專案身分建檔")
        st.write("邏輯開發中：必須連動夥伴清單，確保專案歸屬正確。")
