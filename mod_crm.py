import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴進階維護 (CRM/SRM)</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ 新增合作夥伴", "🔍 夥伴資料庫與風險管理"])
    
    with tab1:
        with st.form("crm_advanced_form", clear_on_submit=True):
            st.subheader("🏢 公司基本資料")
            p_type = st.radio("夥伴類別", ["Customer", "Supplier"], horizontal=True)
            
            c1, c2 = st.columns(2)
            name = c1.text_input("公司全名 (必填)")
            tax_id = c2.text_input("統一編號")
            
            c3, c4 = st.columns(2)
            comp_email = c3.text_input("公司總機電郵")
            comp_phone = c4.text_input("公司總機電話")
            
            address = st.text_input("公司登記地址")

            st.divider()
            st.subheader("👤 窗口聯絡資訊")
            l1, l2, l3 = st.columns(3)
            contact = l1.text_input("聯絡人姓名")
            title = l2.text_input("職稱")
            mobile = l3.text_input("手機號碼")
            email = st.text_input("聯絡人個人電郵")

            st.divider()
            st.subheader("⚠️ 風險與交易設定")
            t1, t2 = st.columns([2, 1])
            trade_items = t1.text_input("交易項目 (例如：真空零件、鍍膜服務)")
            credit_limit = t2.number_input("建議交易金額上限 (未稅)", min_value=0.0, step=10000.0, help="超過此金額的訂單/採購將觸發系統警示")
            
            remarks = st.text_area("備註事項")
            
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
                        supabase.table("partners").upsert(data).execute()
                        st.success(f"✅ {name} 資料已更新，交易上限設定為 ${credit_limit:,.0f}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"存檔失敗：{e}")

    with tab2:
        res = supabase.table("partners").select("*").order("name").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            
            # 視覺化篩選
            search_name = st.text_input("🔍 輸入關鍵字搜尋夥伴...")
            if search_name:
                df = df[df['name'].str.contains(search_name, na=False)]
            
            # 格式化顯示
            display_cols = ["type", "name", "tax_id", "contact_person", "credit_limit", "trade_items"]
            st.dataframe(
                df[display_cols].style.format({"credit_limit": "{:,.0f}"}),
                use_container_width=True,
                hide_index=True
            )
            
            st.divider()
            st.subheader("🗑️ 資料異動管理")
            col_sel, col_btn = st.columns([3, 1])
            target = col_sel.selectbox("選擇管理對象", [""] + df["name"].tolist())
            if target:
                if col_btn.button(f"永久刪除 {target}", type="secondary"):
                    try:
                        supabase.table("partners").delete().eq("name", target).execute()
                        st.warning(f"已從系統移除 {target}")
                        st.rerun()
                    except:
                        st.error("此夥伴已有專案連結，為保護數據完整性，請先刪除關聯專案。")
        else:
            st.info("目前夥伴資料庫為空，請由左側標籤新增。")
