import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴進階管理 (CRM/SRM)</p>', unsafe_allow_html=True)

    # --- 自動測試按鈕 ---
    with st.sidebar:
        st.subheader("🛠️ 開發者工具")
        if st.button("🚀 載入全欄位測試數據"):
            st.session_state.edit_data = {
                "name": "宏達工業股份有限公司", "tax_id": "12345678",
                "comp_email": "office@honda-ind.com", "comp_phone": "02-2233-4455",
                "addr": "台北市大安區信義路四段100號", "contact": "王大明", 
                "mobile": "0912-345-678", "limit": 500000.0, "items": "精密零件"
            }
            st.rerun()

    # 抓取資料
    res = supabase.table("partners").select("*").order("name").execute()
    df = pd.DataFrame(res.data) if res.data else pd.DataFrame()

    tab1, tab2 = st.tabs(["✍️ 編輯與新增", "📊 夥伴清單"])

    with tab1:
        # 修改邏輯：點選下拉選單自動帶入資料
        target = st.selectbox("🎯 選擇既有夥伴進行修改 (留空則為新增)", [""] + (df["name"].tolist() if not df.empty else []))
        if target:
            row = df[df['name'] == target].iloc[0]
            st.session_state.edit_data = {
                "name": row['name'], "tax_id": row['tax_id'], "comp_email": row['company_email'],
                "comp_phone": row['company_phone'], "addr": row['company_address'],
                "contact": row['contact_person'], "mobile": row['contact_mobile'],
                "limit": float(row['credit_limit']), "items": row['trade_items']
            }

        v = st.session_state.get("edit_data", {})
        with st.form("crm_form"):
            c1, c2, c3 = st.columns([2, 1, 1])
            name = c1.text_input("公司名稱", value=v.get("name", ""), disabled=True if target else False)
            tax_id = c2.text_input("統一編號", value=v.get("tax_id", ""))
            limit = c3.number_input("建議交易上限", value=v.get("limit", 0.0))
            
            addr = st.text_input("公司地址", value=v.get("addr", ""))
            
            l1, l2, l3 = st.columns(3)
            contact = l1.text_input("聯絡人", value=v.get("contact", ""))
            mobile = l2.text_input("手機", value=v.get("mobile", ""))
            items = l3.text_input("交易項目", value=v.get("items", ""))

            if st.form_submit_button("💾 儲存資料"):
                save_data = {
                    "name": name, "tax_id": tax_id, "credit_limit": limit,
                    "company_address": addr, "contact_person": contact,
                    "contact_mobile": mobile, "trade_items": items
                }
                # 使用 upsert 根據 name 更新
                supabase.table("partners").upsert(save_data, on_conflict="name").execute()
                st.success("✅ 資料同步成功！")
                st.session_state.edit_data = {}
                st.rerun()

    with tab2:
        if not df.empty:
            st.dataframe(df[["name", "tax_id", "credit_limit", "contact_person"]], use_container_width=True)
            if st.button("🗑️ 刪除已選夥伴") and target:
                supabase.table("partners").delete().eq("name", target).execute()
                st.rerun()
