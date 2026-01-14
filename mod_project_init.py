import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown(f'<p class="main-header">🚀 {dept} 專案身分管理</p>', unsafe_allow_html=True)
    
    # 獲取夥伴清單
    res_p = supabase.table("partners").select("name").eq("type", "Customer").execute()
    cust_list = [p['name'] for p in res_p.data] if res_p.data else []

    tab1, tab2 = st.tabs(["➕ 新增專案", "🔍 現有專案維護"])
    
    with tab1:
        if not cust_list:
            st.warning("⚠️ 請先至『合作夥伴管理』建立客戶資料。")
        else:
            with st.form("add_p_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                p_id = c1.text_input("專案編號 (2026-HTT-001)")
                p_name = c2.text_input("專案名稱")
                
                c3, c4 = st.columns(2)
                customer = c3.selectbox("對應客戶", cust_list)
                p_budget = c4.number_input("合約預算 (未稅)", min_value=0.0)
                
                p_year = st.selectbox("會計年度", [2026, 2027, 2028])
                
                if st.form_submit_button("💾 建立專案"):
                    data = {
                        "project_id": p_id, "project_name": p_name, 
                        "customer_name": customer, "dept": dept, 
                        "year": p_year, "total_budget": p_budget
                    }
                    supabase.table("projects").upsert(data).execute()
                    st.success(f"✅ 專案 {p_id} 已就緒")
                    st.rerun()

    with tab2:
        res = supabase.table("projects").select("*").eq("dept", dept).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df[["project_id", "project_name", "customer_name", "total_budget"]], use_container_width=True)
            
            target_del = st.selectbox("選擇要刪除的專案", [""] + df["project_id"].tolist())
            if target_del:
                if st.button(f"🗑️ 永久刪除 {target_del}"):
                    supabase.table("projects").delete().eq("project_id", target_del).execute()
                    st.rerun()
        else:
            st.info("尚無專案")
