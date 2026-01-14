import streamlit as st
from supabase import create_client

# --- 1. 資料庫連線核心 ---
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error("🚨 Supabase 連線失敗，請檢查 .streamlit/secrets.toml 設定")
        return None

# --- 2. 獲取部門 (目前預設 HTT) ---
def get_dept():
    # 未來可擴充為從使用者登入資訊獲取
    return "HTT"

# --- 3. 全域樣式修復 (移除亂碼源頭) ---
def apply_custom_style():
    st.markdown("""
        <style>
        /* 調整主容器寬度與邊距 */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }
        
        /* 標題樣式 */
        .main-header {
            font-size: 28px;
            font-weight: 700;
            color: #1E1E1E;
            margin-bottom: 20px;
            border-left: 5px solid #FF4B4B;
            padding-left: 10px;
        }

        /* 移除導致亂碼的 Expander 箭頭客製化 CSS */
        /* 回歸 Streamlit 原生樣式，確保穩定性 */
        
        /* 表格優化 */
        .stDataFrame {
            border: 1px solid #f0f0f0;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
