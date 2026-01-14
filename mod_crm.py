import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴進階維護 (CRM/SRM)</p>', unsafe_allow_html=True)
    
    # --- 自動測試工具 ---
    with st.sidebar:
        st.subheader("🛠️ 開發者工具")
        if st.button("🚀 載入 CRM 測試數據"):
            st.session_state.crm_test = {
                "name": "宏達工業股份有限公司",
                "tax_id": "12345678",
                "comp_email": "office@honda-ind.com",
                "comp_phone": "02-2233-4455",
                "addr": "台北市大安區信義路四段100號",
                "contact": "王大明", "title": "採購經理",
                "mobile": "0912-345-678", "mail": "wang.dm@honda-ind.com",
                "items": "精密陶瓷零件", "limit": 500000.0,
                "rem": "測試數據：本公司長期合作夥伴。"
            }
            st.rerun()

    tab1, tab2 = st.tabs(["➕ 新增合作夥伴", "🔍 夥伴資料庫與風險管理"])
    
    with tab1:
        v = st.session_state.get('crm_test', {})
        with st.form("crm_form", clear_on_submit=True):
            p_type = st.radio("夥伴類別", ["Customer", "Supplier"], horizontal=True)
            c1, c2 = st.columns(2)
            name = c1.text_input("公司全名 (必填)", value=v.get("name", ""))
            tax_id = c2.text_input("統一編號", value=v.get("tax_id", ""))
            
            st.divider()
            l1, l2 = st.columns([2, 1])
            trade_items = l1.text_input("交易項目", value=v.get("items", ""))
            credit_limit = l2.number_input("建議交易金額上限", min_value=0.0, value=v.get("limit", 0.0))
            
            if st.form_submit_button("💾 儲存資料"):
                if not name:
                    st.error("❌ 公司名稱為必填")
                else:
                    data = {"type": p_type, "name": name, "tax_id": tax_id, "credit_limit": credit_limit, "trade_items": trade_items}
                    supabase.table("partners").upsert(data).execute()
                    st.success(f"✅ {name} 儲存成功")
                    st.rerun()

    with tab2:
        res = supabase.table("partners").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df[["type", "name", "credit_limit", "trade_items"]], use_container_width=True)
        else:
            st.info("資料庫目前為空。")
