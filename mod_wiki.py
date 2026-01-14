import streamlit as st

def show():
    st.markdown('<p class="main-header">🛡️ HTX ERP 開發者地圖 - 業務邏輯鎖定區</p>', unsafe_allow_html=True)
    
    # 鎖定狀態控制 (模擬鎖定鈕功能)
    if "wiki_locked" not in st.session_state:
        st.session_state.wiki_locked = True
    
    lock_status = "🔒 已鎖定" if st.session_state.wiki_locked else "🔓 已解鎖"
    if st.button(f"{lock_status} (點擊解鎖需先與開發者討論)"):
        if st.session_state.wiki_locked:
            st.warning("⚠️ 警告：解鎖將允許變更核心框架邏輯，請確保已完成討論。")
            st.session_state.wiki_locked = False
        else:
            st.session_state.wiki_locked = True
        st.rerun()

    st.divider()

    # 夥伴管理規格 - 強制原子化
    st.success("### 📂 夥伴管理模組 (CRM/SRM) - 原子化欄位清單")
    st.markdown("""
    | 分類 | 鎖定欄位名稱 | 資料類型 | 說明 (一格一資訊) |
    | :--- | :--- | :--- | :--- |
    | **基本** | `comp_name` | String (PK) | 公司全稱 |
    | **基本** | `tax_id` | String | 統一編號 |
    | **聯繫** | `comp_tel` | String | **公司總機電話** (獨立) |
    | **聯繫** | `comp_email` | String | **公司官方/財務電郵** (獨立) |
    | **聯繫** | `contact_name` | String | 主要聯絡人姓名 |
    | **聯繫** | `contact_email` | String | **聯絡人個人電郵** (獨立) |
    | **風險** | `credit_limit` | Float | 建議交易金額上限 |
    """)
    
    if st.session_state.wiki_locked:
        st.info("ℹ️ 當前處於鎖定狀態：AI 禁止私自刪除或合併上述欄位。")
