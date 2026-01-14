import streamlit as st

def show(supabase, dept):
    st.markdown(f'<p class="main-header">📅 {dept} 預算與現金流規劃</p>', unsafe_allow_html=True)
    
    # --- 開發者工具 ---
    with st.sidebar:
        st.subheader("🛠️ 開發者工具")
        if st.button("🚀 載入全表測試數據"):
            st.session_state.test_val = {
                "ar_cust": 850000.0, "ar_rel": 50000.0, "loan": 200000.0,
                "sal_p": 150000.0, "ops_p": 35000.0, "tax_p": 12000.0,
                "rem": "Antigravity：自動生成的 2026 預算測試數據。"
            }
            st.rerun()
        if st.button("🧹 清空"):
            st.session_state.test_val = {}
            st.rerun()

    # --- 1. 時間與標籤 ---
    c1, c2, c3 = st.columns(3)
    year = c1.selectbox("選擇年度", [2026, 2027, 2028])
    month = c2.selectbox("選擇月份", [f"{i:02d}" for i in range(1, 13)])
    project = c3.text_input("專案編號 (選填)", value="GENERAL")

    # --- 2. Cash In 區塊 ---
    st.markdown("### 🟡 Cash In (應收/借款/利息)")
    with st.container(border=True):
        i1, i2, i3 = st.columns(3)
        v = st.session_state.get('test_val', {})
        ar_cust = i1.number_input("AR-Customer", min_value=0.0, value=v.get('ar_cust', 0.0), key="in1")
        ar_rel = i2.number_input("AR-Related Parties", min_value=0.0, value=v.get('ar_rel', 0.0), key="in2")
        loan_in = i3.number_input("Loan (借款收入)", min_value=0.0, value=v.get('loan', 0.0), key="in3")

    # --- 3. Cash Out 區塊 ---
    st.markdown("### 🔴 Cash Out (營運/薪資/稅款)")
    tab1, tab2 = st.tabs(["📌 預計支出 (Plan)", "✅ 實際支出 (Real)"])
    
    with tab1:
        p1, p2, p3 = st.columns(3)
        sal_p = p1.number_input("Salary (薪資) - 預計", min_value=0.0, value=v.get('sal_p', 0.0), key="out1")
        ops_p = p2.number_input("Operating EXP - 預計", min_value=0.0, value=v.get('ops_p', 0.0), key="out2")
        tax_p = p3.number_input("Tax (稅款) - 預計", min_value=0.0, value=v.get('tax_p', 0.0), key="out3")

    # --- 4. 存檔與備註 ---
    st.divider()
    remarks = st.text_area("備註事項", value=v.get('rem', ""))
    
    if st.button("💾 儲存並更新現金流數據", type="primary", use_container_width=True):
        st.success(f"已成功對齊年度 {year}-{month} 之科目。 (資料庫寫入功能下章開啟)")
