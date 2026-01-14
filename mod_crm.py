import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴管理 (CRM/SRM) - 原子化欄位版</p>', unsafe_allow_html=True)

    with st.sidebar:
        if st.button("🚀 載入全原子化測試數據"):
            st.session_state.edit_crm = {
                "name": "宏達工業股份有限公司", "tax_id": "12345678",
                "c_mail": "info@honda.com", "f_mail": "accounting@honda.com",
                "c_phone": "02-22334455", "addr": "台北市大安區...",
                "c_name": "王大明", "c_mobile": "0912-345678", "p_mail": "wang@honda.com",
                "limit": 500000.0, "items": "真空設備"
            }
            st.rerun()

    res = supabase.table("partners").select("*").order("name").execute()
    df = pd.DataFrame(res.data) if res.data else pd.DataFrame()

    tab1, tab2 = st.tabs(["✍️ 編輯與新增", "📊 夥伴資料清單"])

    with tab1:
        target = st.selectbox("🎯 選擇夥伴進行修改", [""] + (df["name"].tolist() if not df.empty else []))
        if target:
            row = df[df['name'] == target].iloc[0]
            st.session_state.edit_crm = {
                "name": row['name'], "tax_id": row['tax_id'], 
                "c_mail": row.get('company_email'), "f_mail": row.get('finance_email'),
                "c_phone": row.get('company_phone'), "addr": row.get('company_address'),
                "c_name": row.get('contact_person'), "c_mobile": row.get('contact_mobile'),
                "p_mail": row.get('contact_email'), "limit": float(row.get('credit_limit', 0)),
                "items": row.get('trade_items')
            }

        v = st.session_state.get("edit_crm", {})
        with st.form("crm_atomic_form"):
            st.subheader("🏢 企業通訊資訊")
            c1, c2, c3 = st.columns([2, 1, 1])
            name = c1.text_input("公司全名", value=v.get("name", ""), disabled=True if target else False)
            tax_id = c2.text_input("統一編號", value=v.get("tax_id", ""))
            limit = c3.number_input("建議交易上限", value=v.get("limit", 0.0))
            
            c4, c5, c6 = st.columns(3)
            comp_email = c4.text_input("公司電郵 (通用)", value=v.get("c_mail", ""))
            fin_email = c5.text_input("財務電郵 (對帳用)", value=v.get("f_mail", ""))
            comp_phone = c6.text_input("公司電話", value=v.get("c_phone", ""))
            
            address = st.text_input("公司地址", value=v.get("addr", ""))
            
            st.divider()
            st.subheader("👤 窗口資訊")
            l1, l2, l3 = st.columns(3)
            c_name = l1.text_input("窗口姓名", value=v.get("c_name", ""))
            c_mobile = l2.text_input("窗口手機", value=v.get("c_mobile", ""))
            c_email = l3.text_input("窗口個人電郵", value=v.get("p_mail", ""))

            if st.form_submit_button("💾 儲存並檢查原子化欄位"):
                save_data = {
                    "name": name, "tax_id": tax_id, "company_email": comp_email,
                    "finance_email": fin_email, "company_phone": comp_phone,
                    "company_address": address, "contact_person": c_name,
                    "contact_mobile": c_mobile, "contact_email": c_email,
                    "credit_limit": limit, "trade_items": v.get("items", "")
                }
                supabase.table("partners").upsert(save_data, on_conflict="name").execute()
                st.success(f"✅ {name} 資料已拆解存檔。")
                st.session_state.edit_crm = {}
                st.rerun()

    with tab2:
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
