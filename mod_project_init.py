import streamlit as st
import pandas as pd
import time

def show(supabase):
    st.markdown('<p class="main-header">🚀 專案身分建檔 (Project Identity)</p>', unsafe_allow_html=True)

    # --- 1. 讀取 CRM 客戶資料 (連動下拉) ---
    try:
        res = supabase.table("partners").select("id, name").eq("type", "Customer").execute()
        customers = {row['name']: row['id'] for row in res.data}
    except Exception as e:
        st.error(f"讀取客戶資料失敗: {e}")
        customers = {}

    # --- 2. 建立表單 (使用 Session State 保持輸入狀態) ---
    if "proj_form" not in st.session_state:
        st.session_state.proj_form = {"items": pd.DataFrame(columns=["item_name", "quantity"])}
    
    form_data = st.session_state.proj_form

    with st.expander("📝 建立新專案 (點擊展開)", expanded=True):
        with st.form("project_create_form"):
            c1, c2 = st.columns([2, 1])
            p_code = c1.text_input("專案代號 (Project Code)", 
                                   value=form_data.get("code", ""),
                                   placeholder="範例: SLS-MFG-Miz-2601",
                                   help="[類型]-[部門]-[客戶]-[年份][序號]")
            
            cust_name = c2.selectbox("客戶 (Customer)", [""] + list(customers.keys()))
            
            st.divider()
            
            c3, c4, c5 = st.columns(3)
            p_name = c3.text_input("專案名稱", value=form_data.get("name", ""))
            p_grade = c4.selectbox("訂單等級", ["A", "B", "C", "D"], index=0)
            p_mode = c5.selectbox("交易模式", ["收訂金", "月結30", "月結60", "其他"], index=2)
            
            d1, d2 = st.columns(2)
            start_d = d1.date_input("開案日")
            end_d = d2.date_input("預計結案日")

            st.subheader("📦 產品動態清單")
            edited_df = st.data_editor(
                form_data.get("items"),
                num_rows="dynamic",
                column_config={
                    "item_name": st.column_config.TextColumn("產品項目名稱", required=True),
                    "quantity": st.column_config.NumberColumn("件數", min_value=1, required=True, default=1)
                },
                use_container_width=True
            )

            submitted = st.form_submit_button("💾 建立專案身分")

            if submitted:
                if not p_code or not p_name or not cust_name:
                    st.error("❌ 專案代號、名稱與客戶為必填欄位！")
                else:
                    try:
                        # 1. 寫入主表 Projects
                        proj_data = {
                            "project_code": p_code,
                            "project_name": p_name,
                            "cust_id": customers[cust_name],
                            "order_grade": p_grade,
                            "trade_mode": p_mode,
                            "start_date": str(start_d),
                            "end_date": str(end_d)
                        }
                        supabase.table("projects").upsert(proj_data).execute()

                        # 2. 寫入子表 Project Items
                        # 先清舊再寫新
                        supabase.table("project_items").delete().eq("project_code", p_code).execute()
                        
                        items_to_insert = []
                        if not edited_df.empty:
                            for _, row in edited_df.iterrows():
                                if row.get("item_name"): 
                                    items_to_insert.append({
                                        "project_code": p_code,
                                        "item_name": row["item_name"],
                                        "quantity": int(row["quantity"])
                                    })
                        
                        if items_to_insert:
                            supabase.table("project_items").insert(items_to_insert).execute()

                        st.toast(f"✅ 專案 {p_code} 建立成功！")
                        time.sleep(1)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"寫入資料庫失敗: {e}")

    # --- 3. 專案列表與管理區 (改為卡片式顯示以便管理) ---
    st.divider()
    st.subheader("📋 已建檔專案清單")
    
    # 查詢專案並關聯客戶名稱
    try:
        res = supabase.table("projects").select("project_code, project_name, order_grade, start_date, partners(name)").order("created_at", desc=True).execute()
        
        if res.data:
            for r in res.data:
                # 卡片容器
                with st.container(border=True):
                    col_main, col_info, col_action = st.columns([3, 2, 1])
                    
                    # 專案資訊
                    cust_name_str = r['partners']['name'] if r['partners'] else "無客戶"
                    col_main.markdown(f"**{r['project_code']}**")
                    col_main.caption(f"{cust_name_str} | {r['project_name']}")
                    
                    col_info.write(f"等級: {r['order_grade']}")
                    col_info.caption(f"開案: {r['start_date']}")
                    
                    # 刪除與管理區
                    with st.expander(f"⚙️ 管理 {r['project_code']}"):
                        st.warning("⚠️ 危險操作區")
                        st.write("刪除專案將一併清除：")
                        st.markdown("- 該專案的所有產品清單")
                        st.markdown("- 該專案的 36個月預算數據")
                        
                        # 刪除按鈕 (使用 Unique Key)
                        if st.button(f"🗑️ 永久刪除", key=f"del_{r['project_code']}"):
                            try:
                                supabase.table("projects").delete().eq("project_code", r['project_code']).execute()
                                st.success(f"已刪除 {r['project_code']} 及其所有關聯資料。")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"刪除失敗: {e}")
        else:
            st.info("目前沒有專案資料。")

    except Exception as e:
        st.error(f"讀取列表失敗: {e}")
