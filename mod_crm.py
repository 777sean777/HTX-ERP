import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴管理 (CRM/SRM) - 依憲修正版</p>', unsafe_allow_html=True)

    # --- 1. 資料庫即時讀取 ---
    res = supabase.table("partners").select("*").order("name").execute()
    df_all = pd.DataFrame(res.data) if res.data else pd.DataFrame()

    # --- 2. 編輯/新增區 (Expander 模式) ---
    with st.expander("▶️ 錄入/修改夥伴細節 (符合原子化規格)", expanded=False):
        # 選擇欲修改對象
        target = st.selectbox("🎯 選擇欲修改對象 (留空為新增)", [""] + (df_all["name"].tolist() if not df_all.empty else []))
        v = df_all[df_all['name'] == target].iloc[0] if target else {}

        with st.form("crm_atomic_form_v3"):
            st.subheader("🏢 公司主體資訊")
            p_type = st.radio("身分分類 (Mandatory)", ["Customer", "Supplier"], horizontal=True, 
                              index=0 if v.get('type')=='Customer' else 1)
            
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("公司全名", value=v.get("name", ""), disabled=True if target else False)
            nation = c2.text_input("公司國籍", value=v.get("nationality", ""))
            tax_id = c3.text_input("統一編號", value=v.get("tax_id", ""))
            
            addr = st.text_input("公司地址", value=v.get("company_address", ""))
            
            c4, c5, c6 = st.columns(3)
            phone = c4.text_input("公司總機", value=v.get("company_phone", ""))
            mail = c5.text_input("公司通用電郵", value=v.get("company_email", ""))
            limit = c6.number_input("建議交易金額上限 (Credit Limit)", value=float(v.get("credit_limit", 0)))

            st.divider()
            # 財務窗口 (符合憲法第3條)
            f_col, s_col = st.columns(2)
            with f_col:
                st.subheader("💰 財務聯絡窗口")
                f_n = st.text_input("財務姓名 (fin_name)", value=v.get("finance_person", ""))
                f_e = st.text_input("財務電郵 (fin_email)", value=v.get("finance_email", ""))
                f_p = st.text_input("財務電話 (fin_phone)", value=v.get("finance_phone", "")) # 憲法補足項
            
            # 業務窗口 (符合憲法第4條)
            with s_col:
                st.subheader("🤝 業務聯絡窗口")
                s_n = st.text_input("業務姓名 (sales_name)", value=v.get("contact_person", ""))
                s_e = st.text_input("業務電郵 (sales_email)", value=v.get("contact_email", ""))
                s_m = st.text_input("業務手機 (sales_mobile)", value=v.get("contact_mobile", ""))
            
            st.divider()
            items = st.text_input("交易項目 (trade_items)", value=v.get("trade_items", ""))
            remark = st.text_area("備註 (remarks)", value=v.get("remarks", ""))
            
            if st.form_submit_button("💾 執行依憲存檔"):
                save_data = {
                    "type": p_type, "name": name, "nationality": nation, "tax_id": tax_id,
                    "company_address": addr, "company_phone": phone, "company_email": mail,
                    "credit_limit": limit, "finance_person": f_n, "finance_email": f_e, "finance_phone": f_p,
                    "contact_person": s_n, "contact_email": s_e, "contact_mobile": s_m,
                    "trade_items": items, "remarks": remark
                }
                supabase.table("partners").upsert(save_data, on_conflict="name").execute()
                st.success(f"✅ 夥伴 {name} 資料已根據憲法規格同步更新")
                st.rerun()

    # --- 3. 檢索與卡片式看板 ---
    st.divider()
    search = st.text_input("🔍 快速檢索 (公司、國籍、項目或窗口)...").strip()
    
    if not df_all.empty:
        # 篩選邏輯
        mask = df_all.apply(lambda r: search.lower() in str(r).lower(), axis=1)
        filtered = df_all[mask]
        
        for _, row in filtered.iterrows():
            with st.container(border=True):
                col_h, col_l = st.columns([4, 1])
                badge = "🟦 客戶" if row['type'] == 'Customer' else "🟧 供應商"
                col_h.markdown(f"#### {badge} | {row['name']} ({row['nationality']})")
                col_l.markdown(f"**交易上限:** `${row['credit_limit']:,.0f}`")
                
                # 精簡模式，點擊才展開
                with st.expander("▶️ 點擊檢閱完整聯絡規格"):
                    d1, d2 = st.columns(2)
                    with d1:
                        st.write(f"**統編:** {row['tax_id']}")
                        st.write(f"**公司電郵:** {row['company_email']}")
                        st.markdown(f"**💰 財務:** {row['finance_person']} / {row['finance_email']} ({row.get('finance_phone')})")
                    with d2:
                        st.write(f"**公司地址:** {row['company_address']}")
                        st.write(f"**交易項目:** {row['trade_items']}")
                        st.markdown(f"**🤝 業務:** {row['contact_person']} / {row['contact_mobile']} / {row['contact_email']}")
                    
                    st.caption(f"備註: {row['remarks']}")
                    
                    if st.button("🗑️ 刪除", key=f"del_{row['name']}"):
                        supabase.table("partners").delete().eq("name", row['name']).execute()
                        st.rerun()
    else:
        st.info("尚無夥伴資料，請展開上方選單新增。")
