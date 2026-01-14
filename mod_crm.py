import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴維護 (CRM/SRM)</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ 新增夥伴", "🔍 夥伴資料庫與維護"])
    
    with tab1:
        with st.form("crm_form", clear_on_submit=True):
            p_type = st.radio("類別", ["Customer", "Supplier"], horizontal=True)
            name = st.text_input("公司名稱 (必填)")
            contact = st.text_input("主要聯絡人")
            tax_id = st.text_input("統一編號")
            
            if st.form_submit_button("💾 儲存夥伴資料"):
                if not name:
                    st.error("❌ 請填寫公司名稱")
                else:
                    data = {"type": p_type, "name": name, "contact_person": contact, "tax_id": tax_id}
                    supabase.table("partners").upsert(data).execute()
                    st.success(f"✅ {name} 已儲存")
                    st.rerun()

    with tab2:
        res = supabase.table("partners").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df[["type", "name", "contact_person", "tax_id"]], use_container_width=True)
            
            # 修改與刪除區
            st.divider()
            col_sel, col_btn = st.columns([3, 1])
            target = col_sel.selectbox("選擇管理對象", [""] + df["name"].tolist())
            if target:
                if col_btn.button(f"🗑️ 刪除 {target}", type="secondary"):
                    try:
                        supabase.table("partners").delete().eq("name", target).execute()
                        st.warning(f"已刪除 {target}")
                        st.rerun()
                    except:
                        st.error("此夥伴已有專案連結，無法刪除")
        else:
            st.info("尚無資料")
