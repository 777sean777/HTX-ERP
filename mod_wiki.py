import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 系統視覺化地圖</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📍 系統架構圖")
        st.graphviz_chart('''
            digraph {
                node [shape=box, style=filled, color=lightblue, fontname="Source Sans Pro"]
                "app.py" -> "core_engine.py" [label="核心"]
                "app.py" -> "mod_wiki.py" [label="說明"]
                "app.py" -> "mod_cashflow.py" [label="財務"]
                "mod_cashflow.py" -> "transactions" [label="存入"]
                "transactions" -> "看板" [label="計算"]
            }
        ''')

    with col2:
        st.subheader("📚 檔案與邏輯說明")
        with st.expander("📂 app.py (入口)", expanded=True):
            st.write("▼ **功能:** 側邊欄導航、版本控管、部門切換。")
            
        with st.expander("📂 mod_cashflow.py (財務規劃)"):
            st.write("▼ **功能:** 現金估算表輸入、Plan/Real 比對、自動測試按鈕。")

        with st.expander("📂 core_engine.py (引擎)"):
            st.write("▼ **功能:** 資料庫連線、CSS 全域樣式注入。")

    st.divider()
    st.subheader("📌 HTX 開發憲法")
    st.success("1. 穩定優先：不使用不穩定的圖示字體。\n2. 數據至上：所有輸入必須經過 transactions 表歸納。")
