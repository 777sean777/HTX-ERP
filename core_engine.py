import streamlit as st
from supabase import create_client

# --- 1. 資料庫連線核心 ---
def init_connection():
    try:
        # 這裡會抓取 secrets.toml 的設定
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        # 避免在畫面顯示醜醜的錯誤，僅在 Dev 模式或 Console 顯示
        print(f"Supabase 連線失敗: {e}")
        return None

# --- 2. 獲取部門 ---
def get_dept():
    return "HTT"

# --- 3. 全域樣式修復 (已移除亂碼源頭) ---
def apply_custom_style():
    st.markdown("""
        <style>
        /* 調整主容器，讓畫面寬一點，不要浪費兩側空間 */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 95% !important;
        }
        
        /* 標題美化 */
        .main-header {
            font-size: 26px;
            font-weight: 700;
            color: #333;
            margin-bottom: 20px;
            border-left: 6px solid #FF4B4B;
            padding-left: 12px;
        }

        /* 強制隱藏可能導致亂碼的偽元素 */
        div[data-testid="stExpander"] details summary::after {
            content: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
