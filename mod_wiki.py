import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 系統視覺化地圖</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🗺️ 系統架構圖")
        # 視覺化各模組間的邏輯關係
        st.graphviz_chart('''
            digraph {
                node [shape=box, style=filled, color=lightblue, fontname="Source Sans Pro"]
                "app.py" -> "core_engine.py" [label="核心驅動"]
                "app.py" -> "mod_wiki.py" [label="系統說明"]
                "app.py" -> "現金流規劃" [label="預算輸入"]
                "現金流規劃" -> "Supabase (transactions)" [label="存入 Plan"]
                "採購系統" -> "Supabase (transactions)" [label="存入 Real"]
                "Supabase (transactions)" -> "決策看板" [label="B-A-V 對帳"]
            }
        ''')

    with col2:
        st.subheader("📖 檔案邏輯清單")
        with st.expander("📄 app.py (主導航入口)", expanded=True):
            st.write("**功能:** 負責權限控管、部門切換、模組分流。")
            st.code("st.sidebar.radio('功能選單', menu)")
            
        with st.expander("📄 core_engine.py (基礎引擎)"):
            st.write("**功能:** Supabase 連線初始化、CSS 視覺樣式注入。")
            
        with st.expander("📄 requirements.txt (環境配置)"):
            st.write("**功能:** 定義系統運行所需的 Python 套件。")

    st.divider()
    st.subheader("📜 神聖科目字典 (V31.2)")
    st.table({
        "分類": ["R系列", "V系列", "F系列", "Cash Flow"],
        "定義": ["預計收入", "變動成本 (PO相關)", "固定費用 (財務相關)", "業外現金流 (借貸/稅)"],
        "對應資料表": ["transactions", "transactions", "transactions", "financial_activities"]
    })
