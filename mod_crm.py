import streamlit as st
import pandas as pd
import time

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴管理 (CRM)</p>', unsafe_allow_html=True)

    # --- 憲法第貳條：Dev Mode 一鍵填充 ---
    if st.session_state.get("dev_mode", False):
        with st.sidebar:
            st.markdown("### 🛠️ CRM 開發工具")
            if st.button("🚀 生成測試客戶 (Customer)"):
                test_data = {
                    "type": "Customer",
                    "name": "Mizuno (美津濃)",
                    "nationality": "Japan",
                    "tax_id": "JP-88889999",
                    "company_email": "purchase@mizuno.jp",
                    "finance_person": "田中 財務長",
                    "finance_email": "finance@mizuno.jp",
                    "contact_person": "佐藤 經理", 
                    "credit_limit": 2000000.0,
                    "trade_items": "機能布料、運動成衣"
                }
                try:
                    supabase.table("partners").upsert(test_data, on_conflict="name").execute()
                    st.toast("✅ 測試客戶 Mizuno 已生成！")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"生成失敗: {e}")

            if st.button("🚀 生成測試供應商 (Supplier)"):
                test_data_sup = {
                    "type": "Supplier",
                    "name": "台塑化學股份有限公司",
                    "nationality": "Taiwan",
                    "tax_id": "12345678",
                    "contact_person": "王廠長",
                    "credit_limit": 5000000.0,
                    "trade_items": "PP粒、化工原料"
                }
                try:
                    supabase.table("partners").upsert(test_data_sup, on_conflict="name").execute()
                    st.toast("✅ 測試供應商台塑已生成！")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"生成失敗: {e}")

    # --- 1. 讀取資料 ---
    res = supabase.table("partners").select("*").order("name").execute()
    df_all = pd.DataFrame(res.data) if res.data else pd.DataFrame()

    # --- 2. 新增/編輯區 (Expander) ---
    with st.expander("▶️ 新增或修改夥伴資料", expanded=False):
        # 選擇對象
        target = st.selectbox("🎯 選擇對象 (留空為新增)", [""] + (df_all["name"].tolist() if not df_all.empty else []))
        v = df_all[df_all['name'] == target].iloc[0] if target else {}

        with st.form("crm_atomic_form"):
            st.subheader("🏢 公司主體")
            c_type = st.radio("身分", ["Customer", "Supplier"], horizontal=True, 
                              index=0 if v.get('type') != 'Supplier' else 1)
            
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("公司名稱", value=v.get("name", ""), disabled=bool(target))
            nation = c2.text_input("國籍", value=v.get("nationality", ""))
            tax = c3.text_input("統編", value=v.get("tax_id", ""))

            c4, c5, c6 = st.columns(3)
            # 憲法原子化欄位
            limit = c4.number_input("交易上限 (Credit Limit)", value=float(v.get("credit_limit", 0)))
            items = c5.text_input("交易項目", value=v.get("trade_items", ""))
            phone = c6.text_input("總機", value=v.get("company_phone", ""))

            st.divider()
            f_col, s_col = st.columns(2)
            with f_col:
                st.markdown("#### 💰 財務窗口")
                f_n = st.text_input("姓名", value=v.get("finance_person", ""), key="fn")
                f_e = st.text_input("電郵", value=v.get("finance_email", ""), key="fe")
                f_p = st.text_input("電話", value=v.get("finance_phone", ""), key="fp")
            with s_col:
                st.markdown("#### 🤝 業務窗口")
                s_n = st.text_input("姓名", value=v.get("contact_person", ""), key="sn")
                s_e = st.text_input("電郵", value=v.get("contact_email", ""), key="se")
                s_m = st.text_input("手機", value=v.get("contact_mobile", ""), key="sm")

            if st.form_submit_button("💾 儲存資料"):
                save_data = {
                    "type": c_type, "name": name, "nationality": nation, "tax_id": tax,
                    "credit_limit": limit, "trade_items": items, "company_phone": phone,
                    "finance_person": f_n, "finance_email": f_e, "finance_phone": f_p,
                    "contact_person": s_n, "contact_email": s_e, "contact_mobile": s_m
                }
                try:
                    supabase.table("partners").upsert(save_data, on_conflict="name").execute()
                    st.success(f"✅ {name} 儲存成功")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"儲存失敗: {e}")

    # --- 3. 列表顯示 ---
    st.divider()
    if not df_all.empty:
        # 簡單搜尋
        search = st.text_input("🔍 搜尋夥伴...", placeholder="輸入名稱或國籍")
        if search:
            df_all = df_all[df_all.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

        for _, row in df_all.iterrows():
            with st.container(border=True):
                c_head, c_info = st.columns([3, 1])
                badge = "🟦 客戶" if row['type'] == 'Customer' else "🟧 供應商"
                c_head.markdown(f"**{badge} | {row['name']}** <small>({row['nationality']})</small>", unsafe_allow_html=True)
                c_info.markdown(f"額度: `${row['credit_limit']:,.0f}`")
