import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴進階維護 (CRM/SRM)</p>', unsafe_allow_html=True)
    
    # --- 開發者工具 (Antigravity 測試腳本) ---
    with st.sidebar:
        st.subheader("🛠️ 開發者工具")
        if st.button("🚀 載入全欄位測試數據"):
            st.session_state.crm_edit_val = {
                "name": "宏達工業股份有限公司", "tax_id": "12345678",
                "comp_email": "office@honda-ind.com", "comp_phone": "02-2233-4455",
                "addr": "台北市大安區信義路四段100號",
                "contact": "王大明", "title": "採購總監",
                "mobile": "0912-345-678", "mail": "wang.dm@honda-ind.com",
                "items": "精密陶瓷零件、真空電漿設備發包", "limit": 500000.0,
                "rem": "測試：這是一個包含完整聯絡資訊的測試檔案。"
            }
            st.rerun()

    # 從資料庫獲取最新資料
    res = supabase.table("partners").select("*").order("name").execute()
    df = pd.DataFrame(res.data) if res.data else pd.DataFrame()

    tab1, tab2 = st.tabs(["✍️ 編輯與新增夥伴", "🔍 夥伴資料庫與風險看板"])

    with tab1:
        # --- 編輯選擇邏輯 ---
        target_edit = ""
        if not df.empty:
            st.info("💡 提示：若需修改資料，請由下方選單選取既有夥伴。")
            target_edit = st.selectbox("🎯 選擇編輯對象 (留空則為新增模式)", [""] + df["name"].tolist())
            
            if target_edit and (st.session_state.get('last_target') != target_edit):
                row = df[df['name'] == target_edit].iloc[0]
                st.session_state.crm_edit_val = {
                    "name": row['name'], "tax_id": row['tax_id'],
                    "comp_email": row['company_email'], "comp_phone": row['company_phone'],
                    "addr": row['company_address'], "contact": row['contact_person'],
                    "title": row['contact_title'], "mobile": row['contact_mobile'],
                    "mail": row['contact_email'], "items": row['trade_items'],
                    "limit": float(row['credit_limit']), "rem": row['remarks']
                }
                st.session_state.last_target = target_edit
                st.rerun()

        v = st.session_state.get('crm_edit_val', {})

        with st.form("crm_advanced_form"):
            st.subheader("🏢 公司核心資料")
            c_type = st.radio("夥伴類別", ["Customer", "Supplier"], horizontal=True)
            c1, c2, c3 = st.columns([2, 1, 1])
            name = c1.text_input("公司全名", value=v.get("name", ""), disabled=True if target_edit else False)
            tax_id = c2.text_input("統一編號", value=v.get("tax_id", ""))
            limit = c3.number_input("建議交易上限", min_value=0.0, value=v.get("limit", 0.0), step=10000.0)
            
            addr = st.text_input("公司地址", value=v.get("addr", ""))
            
            st.divider()
            st.subheader("👤 聯絡窗口與項目")
            l1, l2, l3, l4 = st.columns([1, 1, 1, 2])
            contact = l1.text_input("聯絡人", value=v.get("contact", ""))
            mobile = l2.text_input("手機", value=v.get("mobile", ""))
            phone = l3.text_input("總機", value=v.get("comp_phone", ""))
            items = l4.text_input("交易項目說明", value=v.get("items", ""))
            
            remarks = st.text_area("備註事項", value=v.get("rem", ""))

            if st.form_submit_button("💾 儲存並同步至雲端"):
                data = {
                    "type": c_type, "name": name, "tax_id": tax_id, "credit_limit": limit,
                    "company_address": addr, "contact_person": contact, "contact_mobile": mobile,
                    "company_phone": phone, "trade_items": items, "remarks": remarks
                }
                supabase.table("partners").upsert(data).execute()
                st.success(f"✅ {name} 資料已更新！")
                st.session_state.crm_edit_val = {}
                st.rerun()

    with tab2:
        if not df.empty:
            st.subheader("📊 夥伴全視角清單")
            # 重新定義要顯示的完整欄位清單
            cols_to_show = {
                "type": "類別",
                "name": "公司名稱",
                "tax_id": "統編",
                "credit_limit": "交易上限",
                "contact_person": "聯絡人",
                "contact_mobile": "手機",
                "trade_items": "交易項目",
                "company_address": "公司地址"
            }
            # 重新命名欄位方便閱讀
            display_df = df[list(cols_to_show.keys())].rename(columns=cols_to_show)
            
            # 使用 st.dataframe 的進階顯示，這會自動處理橫向捲軸
            st.dataframe(
                display_df.style.format({"交易上限": "{:,.0f}"}),
                use_container_width=True,
                height=400,
                hide_index=True
            )
            
            # 導出功能
            csv = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 導出全表 CSV", data=csv, file_name="HTX_Partners_Full.csv")
        else:
            st.info("尚無夥伴資料")
