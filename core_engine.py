import streamlit as st
from supabase import create_client

@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

def apply_custom_style():
    st.markdown("""
        <style>
        /* 提升整體字體清晰度 */
        html, body, [class*="st-"] {
            font-family: "Source Sans Pro", sans-serif;
        }
        /* 大項目的視覺層次感 */
        .main-header {
            font-size: 28px !important;
            font-weight: 700 !important;
            color: #1E3A8A;
            border-left: 8px solid #3B82F6;
            padding-left: 15px;
            margin-bottom: 20px;
        }
        /* 數值顯示強化 */
        .stMetric {
            background-color: #F3F4F6;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

def get_dept():
    dept_options = {
        "🚜 HTT (自動化)": "HTT", 
        "🧬 HX (紡織/鍍膜)": "HX", 
        "🇯🇵 HTX JP (日本貿易)": "HTX_JP", 
        "🏢 CPO (總部)": "CPO"
    }
    choice = st.sidebar.selectbox("切換運營部門", list(dept_options.keys()))
    return dept_options[choice]
