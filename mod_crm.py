import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown(f'<p class="main-header">👥 合作夥伴維護 (CRM/SRM)</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ 新增夥伴", "🔍 夥伴資料庫"])
    
    with tab1:
        with st.form("crm_form", clear_on_submit=True):
            p_type = st.radio("類別", ["Customer", "Supplier"], horizontal=True)
            name = st.text_input("公司名稱")
            contact = st.text_input("主要聯絡人")
            tax_id = st.text_input("統一編號")
            
            if st.form_submit_button("💾 儲存夥伴資料"):
                data = {"type": p_type, "name": name, "contact_person": contact, "tax_id": tax_id}
                supabase.table("partners").upsert(data).execute()
                st.success(f"✅ {name} 已儲存")
                st.rerun()

    with tab2:
        res = supabase.table("partners").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df[["type", "name", "contact_person", "tax_id"]], use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 匯出通訊錄 (CSV)", data=csv, file_name="partners.csv")
