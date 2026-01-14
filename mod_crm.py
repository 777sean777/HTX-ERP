import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴管理 (CRM/SRM) - 原子化專業版</p>', unsafe_allow_html=True)

    # --- 1. 資料讀取 ---
    res = supabase.table("partners").select("*").order("name").execute()
    df_all = pd.DataFrame(res.data) if res.data else pd.DataFrame()

    # --- 2. 編輯/新增區 (Expander 模式) ---
    with st.expander("▶️ 新增或修改夥伴細節資料", expanded=False):
        target = st.selectbox("🎯 選擇欲修改對象 (留空為新增)", [""] + (df_all["name"].tolist() if not df_all.empty else []))
        v = df_all[df_all['name'] == target].iloc[0] if target else {}

        with st.form("crm_atomic_form"):
            st.subheader("🏢 公司主體資訊")
            p_type = st.radio("類別", ["Customer", "Supplier"], horizontal=True, 
                              index=0 if v.get('type')=='Customer' else 1)
            
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("公司名稱", value=v.get("name", ""), disabled=True if target else False)
            nation = c2.text_input("公司國籍", value=v.get("nationality", ""))
            tax_id = c3.text_input("統一編號", value=v.get("tax_id", ""))
            
            addr = st.text_input("公司地址", value=v.get("company_address", ""))
            
            c4, c5, c6 = st.columns([1,1,1])
            phone = c4.text_input("公司總機", value=v.get("company_phone", ""))
            mail = c5.text_input("公司電郵", value=v.get("company_email", ""))
            limit = c6.number_input("建議交易金額上限", value=float(v.get("credit_limit", 0)))

            st.divider()
            f_col, s_col = st.columns(2)
            with f_col:
                st.subheader("💰 財務窗口")
                f_n = st.text_input("財務姓名", value=v.get("finance_person", ""))
                f_e = st.text_input("財務電郵", value=v.get("finance_email", ""))
            with s_col:
                st.subheader("🤝 業務窗口")
                s_n = st.text_input("業務姓名", value=v.get("contact_person", ""))
                s_e = st.text_input("業務電郵", value=v.get("contact_email", ""))
                s_m = st.text_input("業務手機", value=v.get("contact_mobile", ""))
            
            items = st.text_input("交易項目", value=v.get("trade_items", ""))
            remark = st.text_area("備註", value=v.get("remarks", ""))
            
            if st.form_submit_button("💾 儲存原子化檔案"):
                save_data = {
                    "type": p_type, "name": name, "nationality": nation, "tax_id": tax_id,
                    "company_address": addr, "company_phone": phone, "company_email": mail,
                    "credit_limit": limit, "finance_person": f_n, "finance_email": f_e,
                    "contact_person": s_n, "contact_email": s_e, "contact_mobile": s_m,
                    "trade_items": items, "remarks": remark
                }
                supabase.table("partners").upsert(save_data, on_conflict="name").execute()
                st.success("✅ 資料同步成功")
                st.rerun()

    # --- 3. 檢索與精簡卡片看板 ---
    st.divider()
    search = st.text_input("🔍 輸入關鍵字快速檢索 (公司、分類、項目)...")
    
    if not df_all.empty:
        filtered = df_all[df_all.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
        for _, row in filtered.iterrows():
            with st.container(border=True):
                col_h, col_l = st.columns([4, 1])
                badge = "🟦 客戶" if row['type'] == 'Customer' else "🟧 供應商"
                col_h.markdown(f"#### {badge} | {row['name']} ({row['nationality']})")
                col_l.markdown(f"**上限:** `${row['credit_limit']:,.0f}`")
                
                with st.expander("▶️ 點擊查看完整聯絡細節與項目"):
                    st.write(f"**交易項目:** {row['trade_items']}")
                    d1, d2 = st.columns(2)
                    d1.markdown(f"**💰 財務:** {row['finance_person']} / {row['finance_email']}")
                    d2.markdown(f"**🤝 業務:** {row['contact_person']} / {row['contact_mobile']}")
                    st.caption(f"備註: {row['remarks']}")
                    if st.button("🗑️ 刪除", key=f"del_{row['name']}"):
                        supabase.table("partners").delete().eq("name", row['name']).execute()
                        st.rerun()
