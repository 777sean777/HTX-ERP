import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴管理 (CRM/SRM) - 完整欄位版</p>', unsafe_allow_html=True)

    with st.sidebar:
        if st.button("🚀 載入測試數據"):
            st.session_state.edit_crm = {
                "name": "宏達工業股份有限公司", "tax_id": "12345678",
                "c_mail": "finance@honda.com", "c_phone": "02-12345678",
                "addr": "台北市大安區...", "contact": "王大明", 
                "mobile": "0900-111222", "p_mail": "wang@honda.com",
                "items": "真空零件", "limit": 500000.0
            }
            st.rerun()

    # 抓取資料庫清單
    res = supabase.table("partners").select("*").order("name").execute()
    df = pd.DataFrame(res.data) if res.data else pd.DataFrame()

    tab1, tab2 = st.tabs(["✍️ 編輯與新增", "📊 夥伴資料清單"])

    with tab1:
        # 編輯選取邏輯
        target = st.selectbox("🎯 選擇夥伴進行修改 (留空為新增)", [""] + (df["name"].tolist() if not df.empty else []))
        if target:
            row = df[df['name'] == target].iloc[0]
            st.session_state.edit_crm = {
                "name": row['name'], "tax_id": row['tax_id'], "c_mail": row['company_email'],
                "addr": row['company_address'], "contact": row['contact_person'],
                "p_mail": row['contact_email'], "limit": float(row['credit_limit']), "items": row['trade_items']
            }

        v = st.session_state.get("edit_crm", {})
        with st.form("crm_form"):
            c1, c2 = st.columns([2, 1])
            name = c1.text_input("公司全名", value=v.get("name", ""), disabled=True if target else False)
            tax_id = c2.text_input("統一編號", value=v.get("tax_id", ""))
            
            # 補回消失的電郵欄位
            c3, c4 = st.columns(2)
            comp_email = c3.text_input("公司總機/財務電郵", value=v.get("c_mail", ""))
            limit = c4.number_input("建議交易上限", value=v.get("limit", 0.0))
            
            address = st.text_input("地址", value=v.get("addr", ""))
            
            l1, l2, l3 = st.columns(3)
            contact = l1.text_input("聯絡人", value=v.get("contact", ""))
            personal_email = l2.text_input("聯絡人電郵", value=v.get("p_mail", ""))
            trade_items = l3.text_input("交易項目", value=v.get("items", ""))

            if st.form_submit_button("💾 儲存 (包含電郵等全欄位)"):
                save_data = {
                    "name": name, "tax_id": tax_id, "company_email": comp_email,
                    "company_address": address, "contact_person": contact,
                    "contact_email": personal_email, "credit_limit": limit, "trade_items": trade_items
                }
                # 強制使用 on_conflict 解決 Duplicate Error
                supabase.table("partners").upsert(save_data, on_conflict="name").execute()
                st.success("✅ 資料庫全欄位同步成功")
                st.session_state.edit_crm = {}
                st.rerun()

    with tab2:
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
