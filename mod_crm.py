import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴進階維護 (CRM/SRM)</p>', unsafe_allow_html=True)
    
    # --- Antigravity 自動測試工具 ---
    with st.sidebar:
        st.subheader("🛠️ 開發者工具")
        if st.button("🚀 載入 CRM 測試數據"):
            st.session_state.crm_test = {
                "name": "宏達工業股份有限公司",
                "tax_id": "12345678",
                "comp_email": "office@honda-ind.com",
                "comp_phone": "02-2233-4455",
                "addr": "台北市大安區信義路四段100號",
                "contact": "王大明",
                "title": "採購經理",
                "mobile": "0912-345-678",
                "mail": "wang.dm@honda-ind.com",
                "items": "精密陶瓷零件、真空電漿設備",
                "limit": 500000.0,
                "rem": "這是 Antigravity 自動生成的測試夥伴資料。"
            }
            st.rerun()
        if st.button("🧹 清空 CRM 欄位"):
            if 'crm_test' in st.session_state:
                del st.session_state.crm_test
            st.rerun()

    tab1, tab2 = st.tabs(["➕ 新增合作夥伴", "🔍 夥伴資料庫與風險管理"])
    
    with tab1:
        # 讀取測試數據
        v = st.session_state.get('crm_test', {})
        
        with st.form("crm_advanced_form", clear_on_submit=True):
            st.subheader("🏢 公司基本資料")
            p_type = st.radio("夥伴類別", ["Customer", "Supplier"], horizontal=True)
            
            c1, c2 = st.columns(2)
            name = c1.text_input("公司全名 (必填)", value=v.get("name", ""))
            tax_id = c2.text_input("統一編號", value=v.get("tax_id", ""))
            
            c3, c4 = st.columns(2)
            comp_email = c3.text_input("公司總機電郵", value=v.get("comp_email", ""))
            comp_phone = c4.text_input("公司總機電話", value=v.get("comp_phone", ""))
            
            address = st.text_input("公司登記地址", value=v.get("addr", ""))

            st.divider()
            st.subheader("👤 窗口聯絡資訊")
            l1, l2, l3 = st.columns(3)
            contact = l1.text_input("聯絡人姓名", value=v.get("contact", ""))
            title = l2.text_input("職稱", value=v.get("title", ""))
            mobile = l3.text_input("手機號碼", value=v.get("mobile", ""))
            email = st.text_input("聯絡人個人電郵", value=v.get("mail", ""))

            st.divider()
            st.subheader("⚠️ 風險與交易設定")
            t1, t2 = st.columns([2, 1])
            trade_items = t1.text_input("交易項目", value=v.get("items", ""))
            credit_limit = t2.number_input("建議交易金額上限 (未稅)", min_value=0.0, step=10000.0, value=v.get("limit", 0.0))
            
            remarks = st.text_area("備註事項", value=v.get("rem", ""))
            
            if st.form_submit_button("💾 儲存並建立檔案"):
                if not name:
                    st.error("❌ 錯誤：公司名稱為必填項目")
                else:
                    data = {
                        "type": p_type, "name": name, "tax_id": tax_id,
                        "company_email": comp_email, "company_phone": comp_phone,
                        "company_address": address, "contact_person": contact,
                        "contact_title": title, "contact_email": email,
                        "contact_mobile": mobile, "trade_items": trade_items,
                        "credit_limit": credit_limit, "remarks": remarks
                    }
                    try:
                        # 執行資料庫寫入
                        response = supabase.table("partners").upsert(data).execute()
                        st.success(f"✅ 成功：{name} 資料已同步至 Supabase")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        # 詳細報錯回饋
                        st.error(f"🚨 存檔失敗！錯誤原因：{str(e)}")
                        st.warning("提示：請確認 Supabase SQL 是否已正確執行，或統編/名稱是否重複。")

    with tab2:
        try:
            res = supabase.table("partners").select("*").order("name").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                
                # 搜尋功能
                search_name = st.text_input("🔍 輸入關鍵字搜尋 (公司名/聯絡人/統編)...")
                if search_name:
                    df = df[df['name'].str.contains(search_name, na=False) | 
                            df['contact_person'].str.contains(search_name, na=False) |
                            df['tax_id'].str.contains(search_name, na=False)]
                
                # 列表顯示
                st.dataframe(
                    df[["type", "name", "tax_id", "contact_person", "credit_limit", "trade_items"]],
                    use_container_width=True,
                    hide_index=
