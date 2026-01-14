import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown(f'<p class="main-header">📅 {dept} 預算與現金流規劃</p>', unsafe_allow_html=True)
    
    # --- 1. 自動測試與工具區 ---
    with st.sidebar:
        st.subheader("🛠️ 開發者工具")
        if st.button("🚀 載入模擬測試數據"):
            st.session_state.test_val = {
                "ar_cust": 800000.0,
                "salary_p": 120000.0,
                "ops_p": 45000.0,
                "remarks": "Antigravity 自動生成測試數據"
            }
            st.rerun()
        if st.button("🧹 清空欄位"):
            if 'test_val' in st.session_state:
                del st.session_state.test_val
            st.rerun()

    # --- 2. 基礎條件設定 ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        year = c1.selectbox("選擇年度", [2026, 2027, 2028])
        month = c2.selectbox("選擇月份", [f"{i:02d}" for i in range(1, 13)])
        project_id = c3.text_input("專案編號 (選填)", value="GENERAL")
        
    st.divider()

    # --- 3. 現金流入 (Cash In) ---
    st.subheader("💰 Cash In (應收/借款/利息)")
    with st.expander("展開 Cash In 填報", expanded=True):
        i1, i2, i3 = st.columns(3)
        ar_cust = i1.number_input("應收帳款-客戶 (AR-Customer)", min_value=0.0, step=1000.0, key="in_ar", value=st.session_state.get('test_val', {}).get('ar_cust', 0.0))
        ar_related = i2.number_input("應收帳款-關係人", min_value=0.0)
        loan_in = i3.number_input("借款收入 (Loan)", min_value=0.0)
        
        i4, i5, i6 = st.columns(3)
        interest = i4.number_input("利息收入", min_value=0.0)
        tax_refund = i5.number_input("退稅款", min_value=0.0)
        others_in = i6.number_input("其他收入", min_value=0.0)

    # --- 4. 現金流出 (Cash Out - Plan/Real) ---
    st.subheader("💸 Cash Out (營運/薪資/購料)")
    tab_plan, tab_real = st.tabs(["📌 預計支出 (Plan)", "✅ 實際支出 (Real)"])
    
    with tab_plan:
        p1, p2, p3 = st.columns(3)
        salary_p = p1.number_input("薪資 獎金 (Salary) - 預計", min_value=0.0, key="p_sal", value=st.session_state.get('test_val', {}).get('salary_p', 0.0))
        ops_p = p2.number_input("營運支出 (Operating EXP) - 預計", min_value=0.0, key="p_ops", value=st.session_state.get('test_val', {}).get('ops_p', 0.0))
        tax_p = p3.number_input("稅款 (Tax) - 預計", min_value=0.0)
        
    with tab_real:
        st.info("實際支出通常連動 PO 系統，手動填寫僅供調整。")
        r1, r2 = st.columns(2)
        salary_r = r1.number_input("薪資 獎金 (Salary) - 實際", min_value=0.0)
        ops_r = r2.number_input("營運支出 (Operating EXP) - 實際", min_value=0.0)

    # --- 5. 存檔與備註 ---
    st.divider()
    remarks = st.text_area("備註事項 (例如：下月應催發票、催款提醒)", value=st.session_state.get('test_val', {}).get('remarks', ""))
    
    if st.button("💾 儲存本月現金流數據", type="primary", use_container_width=True):
        # 這裡下一階段會實作 Supabase Upsert 邏輯
        st.success(f"已模擬儲存 {year}-{month} 之數據。 (Antigravity 備份完成)")
