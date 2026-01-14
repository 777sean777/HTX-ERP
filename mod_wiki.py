import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 系統視覺化地圖</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🗺️ 系統架構圖")
        st.graphviz_chart('''
            digraph {
                node [shape=box, style=filled, color=lightblue, fontname="Source Sans Pro"]
                "app.py" -> "core_engine.py" [label="核心驅動"]
                "app.py" -> "mod_wiki.py" [label="系統說明"]
                "app.py" -> "mod_cashflow.py" [label="預算/現金流"]
                "mod_cashflow.py" -> "Supabase (transactions)" [label="存入 Plan"]
                "採購系統" -> "Supabase (transactions)" [label="存入 Real"]
                "Supabase (transactions)" -> "決策看板" [label="B-A-V 對帳"]
            }
        ''')

    with col2:
        st.subheader("📖 檔案邏輯清單")
        with st.expander("📄 app.py (主導航入口)", expanded=True):
            st.write("● **功能:** 負責權限控擊、部門切換、模組分流。")
            st.code("st.sidebar.radio('功能選單', menu)")
            
        with st.expander("📄 mod_cashflow.py (現金流規劃)"):
            st.write("● **核心:** 整合 R/V/F/Loan 科目。")
            st.write("● **功能:** 支援 Plan 與 Real 數據輸入，含自動測試按鈕。")

        with st.expander("📄 core_engine.py (基礎引擎)"):
            st.write("● **功能:** Supabase 連線與全域 CSS 樣式設定。")

    st.divider()
    st.subheader("📜 核心憲法備忘錄")
    st.warning("1. 年度斷代：專案 ID 需含年份。 \n2. 唯一索引：transactions 表必須包含 dept, month, code。")
