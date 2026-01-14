import streamlit as st
import pandas as pd
import time

def show(supabase, dept):
    st.markdown('<p class="main-header">👥 合作夥伴管理 (CRM)</p>', unsafe_allow_html=True)

    # --- Dev Mode 生成工具 ---
    if st.session_state.get("dev_mode", False):
        with st.sidebar:
            st.markdown("### 🛠️ CRM 開發工具")
            if st.button("🚀 生成測試客戶 (Customer)"):
                test_data = {
                    "type": "Customer",
                    "name": "Mizuno (美津濃)",
                    "nationality": "Japan",
                    "tax_id": "JP-88889999",
                    "company_email": "purchase@mizuno.jp",
                    "finance_person": "田中 財務長",
                    "finance_email": "finance@mizuno.jp",
                    "finance_phone": "+81-3-1234-5678",
                    "contact_person": "佐藤 經理",
                    "contact_email": "sato@mizuno.jp",
                    "contact_mobile": "0900-111-222", 
                    "credit_limit": 2000000.0,
                    "trade_items": "機能布料、運動成衣",
                    "company_phone": "+81-3-0000-1111",
                    "company_address": "日本大阪府大阪市住之江區"
                }
                try:
                    supabase.table("partners").upsert(test_data, on_conflict="name").execute()
                    st.toast("✅ 測試客戶 Mizuno 已生成！")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"生成失敗: {e}")

    # --- 1. 讀取資料 ---
    try:
        res = supabase.table("partners").select("*").order("name").execute()
        df_all = pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception as e:
        st.error(f"讀取資料庫失敗: {e}")
        df_all = pd.DataFrame()

    # --- 2. 新增/編輯區 ---
    with st.expander("▶️ 新增或修改夥伴資料", expanded=True):
        
        # 選擇對象
        target = st.selectbox("🎯 選擇對象 (留空為新增)", [""] + (df_all["name"].tolist() if not df_all.empty else []), key="crm_target_select")
        
        # 抓取資料邏輯
        v = {}
        if target and not df_all.empty:
            filtered = df_all[df_all['name'] == target]
            if not filtered.empty:
                v = filtered.iloc[0].to_dict()

        # 為了讓輸入框在切換客戶時能自動更新，給每個 widget 一個獨一無二的 key
        k_suffix = str(target) if target else "new"

        with st.form("crm_atomic_form"):
            st.subheader("🏢 公司主體")
            
            type_idx = 1 if v.get('type') == 'Supplier' else 0
            c_type = st.radio("身分", ["Customer", "Supplier"], horizontal=True, index=type_idx, key=f"type_{k_suffix}")
            
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("公司名稱", value=v.get("name", ""), disabled=bool(target), key=f"name_{k_suffix}")
            nation = c2.text_input("國籍", value=v.get("nationality", ""), key=f"nat_{k_suffix}")
            tax = c3.text_input("統編", value=v.get("tax_id", ""), key=f"tax_{k_suffix}")

            addr = st.text_input("公司地址", value=v.get("company_address", ""), key=f"addr_{k_suffix}")

            c4, c5, c6 = st.columns(3)
            limit_val = float(v.get("credit_limit")) if v.get("credit_limit") else 0.0
            limit = c4.number_input("交易上限 (Credit Limit)", value=limit_val, step=10000.0, key=f"limit_{k_suffix}")
            items = c5.text_input("交易項目", value=v.get("trade_items", ""), key=f"items_{k_suffix}")
            phone = c6.text_input("總機", value=v.get("company_phone", ""), key=f"phone_{k_suffix}")
            
            c_mail = st.text_input("公司通用電郵", value=v.get("company_email", ""), key=f"cmail_{k_suffix}")

            st.divider()
            f_col, s_col = st.columns(2)
            with f_col:
                st.markdown("#### 💰 財務窗口")
                f_n = st.text_input("姓名", value=v.get("finance_person", ""), key=f"fn_{k_suffix}")
                f_e = st.text_input("電郵", value=v.get("finance_email", ""), key=f"fe_{k_suffix}")
                f_p = st.text_input("電話", value=v.get("finance_phone", ""), key=f"fp_{k_suffix}")
            with s_col:
                st.markdown("#### 🤝 業務窗口")
                s_n = st.text_input("姓名", value=v.get("contact_person", ""), key=f"sn_{k_suffix}")
                s_e = st.text_input("電郵", value=v.get("contact_email", ""), key=f"se_{k_suffix}")
                s_m = st.text_input("手機", value=v.get("contact_mobile", ""), key=f"sm_{k_suffix}")

            st.markdown("---")
            if st.form_submit_button("💾 儲存資料"):
                save_data = {
                    "type": c_type, "name": name, "nationality": nation, "tax_id": tax,
                    "company_address": addr, "credit_limit": limit, "trade_items": items, 
                    "company_phone": phone, "company_email": c_mail,
                    "finance_person": f_n, "finance_email": f_e, "finance_phone": f_p,
                    "contact_person": s_n, "contact_email": s_e, "contact_mobile": s_m
                }
                try:
                    supabase.table("partners").upsert(save_data, on_conflict="name").execute()
                    st.success(f"✅ {name} 資料已更新！")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"儲存失敗: {e}")

    # --- 3. 列表顯示 (含刪除功能) ---
    st.divider()
    if not df_all.empty:
        st.subheader("📋 夥伴名單")
        search = st.text_input("🔍 搜尋夥伴...", placeholder="輸入名稱或國籍")
        if search:
            df_all = df_all[df_all.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

        for _, row in df_all.iterrows():
            with st.container(border=True):
                c_head, c_info = st.columns([3, 1])
                badge = "🟦 客戶" if row['type'] == 'Customer' else "🟧 供應商"
                nation_str = f"({row.get('nationality', '未知')})"
                c_head.markdown(f"**{badge} | {row['name']}** <small>{nation_str}</small>", unsafe_allow_html=True)
                
                limit_show = float(row.get('credit_limit')) if row.get('credit_limit') else 0
                c_info.markdown(f"額度: `${limit_show:,.0f}`")
                
                # [新增] 刪除功能區
                with st.expander("⚙️ 管理此夥伴"):
                    st.write(f"統一編號: {row.get('tax_id', '無')}")
                    # 使用 row['id'] 作為 key 確保唯一性
                    if st.button(f"🗑️ 永久刪除 {row['name']}", key=f"del_{row['id']}"):
                        try:
                            supabase.table("partners").delete().eq("id", row['id']).execute()
                            st.warning(f"已刪除 {row['name']}")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"刪除失敗 (可能已被專案引用): {e}")
