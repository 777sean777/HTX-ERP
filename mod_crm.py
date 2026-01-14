import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴管理 (CRM/SRM) - 精簡看板版</p>', unsafe_allow_html=True)

    # --- 1. 建立/編輯區 ---
    with st.expander("➕ 新增 / ✍️ 編輯 夥伴資料", expanded=False):
        res = supabase.table("partners").select("*").order("name").execute()
        df_all = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        
        target = st.selectbox("🎯 選擇對象進行修改 (留空為新增)", [""] + (df_all["name"].tolist() if not df_all.empty else []))
        v = {}
        if target:
            row = df_all[df_all['name'] == target].iloc[0]
            v = row # 這裡取得資料庫現有值

        with st.form("crm_form_v2"):
            p_type = st.radio("類別", ["Customer", "Supplier"], horizontal=True, index=0 if v.get('type')=='Customer' else 1)
            c1, c2, c3 = st.columns([2,1,1])
            name = c1.text_input("公司名稱", value=v.get("name", ""), disabled=True if target else False)
            tax_id = c2.text_input("統一編號", value=v.get("tax_id", ""))
            limit = c3.number_input("交易上限", value=float(v.get("credit_limit", 0)))

            st.markdown("---")
            col_fin, col_sales = st.columns(2)
            with col_fin:
                st.subheader("💰 財務聯絡人")
                f_name = st.text_input("財務姓名", value=v.get("finance_person", ""))
                f_mail = st.text_input("財務電郵", value=v.get("finance_email", ""))
            with col_sales:
                st.subheader("🤝 業務聯絡人")
                s_name = st.text_input("業務姓名", value=v.get("contact_person", ""))
                s_mail = st.text_input("業務電郵", value=v.get("contact_email", ""))
                s_phone = st.text_input("業務手機", value=v.get("contact_mobile", ""))
            
            remark = st.text_area("備註", value=v.get("remarks", ""))
            
            if st.form_submit_button("💾 儲存資料"):
                save_data = {
                    "name": name, "type": p_type, "tax_id": tax_id, "credit_limit": limit,
                    "finance_person": f_name, "finance_email": f_mail,
                    "contact_person": s_name, "contact_email": s_mail, "contact_mobile": s_phone,
                    "remarks": remark
                }
                supabase.table("partners").upsert(save_data, on_conflict="name").execute()
                st.success("✅ 資料同步成功")
                st.rerun()

    # --- 2. 檢索與精簡看板 ---
    st.divider()
    search = st.text_input("🔍 快速檢索 (輸入公司名、分類、或窗口)...")
    
    if not df_all.empty:
        # 篩選邏輯
        filtered_df = df_all[df_all.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
        
        for idx, row in filtered_df.iterrows():
            with st.container(border=True):
                # 精簡標題列
                label = "🟦 客戶" if row['type'] == 'Customer' else "🟧 供應商"
                col_head, col_limit = st.columns([3, 1])
                with col_head:
                    st.markdown(f"#### {label} | {row['name']}")
                with col_limit:
                    st.markdown(f"**交易上限:** `${row['credit_limit']:,.0f}`")
                
                # 點擊展開詳細資訊
                with st.expander("📄 檢視完整細節"):
                    d1, d2 = st.columns(2)
                    d1.write(f"**統編:** {row['tax_id']}")
                    d1.write(f"**財務窗口:** {row.get('finance_person')} ({row.get('finance_email')})")
                    d2.write(f"**業務窗口:** {row.get('contact_person')} ({row.get('contact_mobile')})")
                    st.write(f"**備註:** {row.get('remarks')}")
                    if st.button("🗑️ 刪除夥伴資料", key=f"del_{idx}"):
                        supabase.table("partners").delete().eq("name", row['name']).execute()
                        st.rerun()
    else:
        st.info("資料庫目前為空。")
