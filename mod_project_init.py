import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown(f'<p class="main-header">🚀 {dept} 專案身分管理</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ 新增專案", "🔍 現有專案維護"])
    
    with tab1:
        with st.form("add_project_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            p_id = c1.text_input("專案編號 (例: 2026-HTT-001)")
            p_name = c2.text_input("專案名稱")
            
            c3, c4 = st.columns(2)
            p_year = c3.selectbox("會計年度", [2026, 2027, 2028])
            p_budget = c4.number_input("預計總合約金額 (未稅)", min_value=0.0)
            
            if st.form_submit_button("💾 確認建立專案"):
                if not p_id or not p_name:
                    st.error("❌ 編號與名稱為必填")
                else:
                    data = {
                        "project_id": p_id, "project_name": p_name,
                        "dept": dept, "year": p_year, "total_budget": p_budget
                    }
                    supabase.table("projects").upsert(data).execute()
                    st.success(f"✅ 專案 {p_id} 建立成功")
                    st.rerun()

    with tab2:
        res = supabase.table("projects").select("*").eq("dept", dept).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df[["project_id", "project_name", "year", "total_budget"]], use_container_width=True)
            
            # 刪除邏輯
            target_del = st.selectbox("選擇要刪除的專案 ID", [""] + df["project_id"].tolist())
            if target_del:
                if st.button(f"🗑️ 永久刪除 {target_del}", type="secondary"):
                    supabase.table("projects").delete().eq("project_id", target_del).execute()
                    st.warning("已刪除該專案及其關聯規劃")
                    st.rerun()
        else:
            st.info("尚無專案資料。")
