import streamlit as st
import pandas as pd
import time

def show(supabase):
    st.markdown('<p class="main-header">🚀 專案身分建檔 (Project Identity)</p>', unsafe_allow_html=True)

    # --- 憲法 Dev Mode：測試數據填充 ---
    if st.session_state.get("dev_mode", False):
        with st.sidebar:
            st.markdown("### 🛠️ 開發者工具")
            if st.button("🚀 填入 SLS 測試案"):
                st.session_state.proj_form = {
                    "code": "SLS-MFG-Miz-2601",
                    "name": "Mizuno 2026 年度新款開發案",
                    "grade": "A",
                    "mode": "月結60",
                    "items": pd.DataFrame([
                        {"item_name": "主面料開發", "quantity": 100},
                        {"item_name": "特殊輔料", "quantity": 500}
                    ])
                }
                st.rerun()

    # --- 1. 讀取 CRM 客戶資料 (連動下拉) ---
    try:
        res = supabase.table("partners").select("id, name").eq("type", "Customer").execute()
        customers = {row['name']: row['id'] for row in res.data}
    except:
        customers = {}

    # --- 2. 建立表單 ---
    # 讀取 Session State 或初始化
    form_data = st.session_state.get("proj_form", {
        "items": pd.DataFrame(columns=["item_name", "quantity"])
    })

    with st.form("project_create_form"):
        c1, c2 = st.columns([2, 1])
        # 憲法 4-1: 手動 Project Code
        p_code = c1.text_input("專案代號 (Project Code)", 
                               value=form_data.get("code", ""),
                               placeholder="格式範例: SLS-MFG-Miz-2601",
                               help="[類型]-[部門]-[客戶]-[年份][序號]")
        
        # 憲法 4-1: 客戶連動
        cust_name = c2.selectbox("客戶 (Customer)", [""] + list(customers.keys()))
        
        st.divider()
        
        c3, c4, c5 = st.columns(3)
        p_name = c3.text_input("專案名稱", value=form_data.get("name", ""))
        # 憲法 4-1: 等級 A-D
        p_grade = c4.selectbox("訂單等級", ["A", "B", "C", "D"], index=0 if not form_data.get("grade") else ["A","B","C","D"].index(form_data["grade"]))
        p_mode = c5.selectbox("交易模式", ["收訂金", "月結30", "月結60", "其他"], index=2)
        
        d1, d2 = st.columns(2)
        start_d = d1.date_input("開案日")
        end_d = d2.date_input("預計結案日")

        st.subheader("📦 產品動態清單 (Product List)")
        st.caption("請在此處新增本專案之產品項目與預計件數")
        
        # 憲法 4-1: 動態清單元件
        # 使用 Data Editor 讓使用者可以像 Excel 一樣新增刪除
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

                    # 2. 寫入子表 Project Items (先刪後加，確保一致性)
                    # 先刪除該專案舊有 Item (若是修改模式)
                    supabase.table("project_items").delete().eq("project_code", p_code).execute()
                    
                    # 準備新 Item 資料
                    items_to_insert = []
                    if not edited_df.empty:
                        for _, row in edited_df.iterrows():
                            if row["item_name"]: # 確保有名稱
                                items_to_insert.append({
                                    "project_code": p_code,
                                    "item_name": row["item_name"],
                                    "quantity": int(row["quantity"])
                                })
                    
                    if items_to_insert:
                        supabase.table("project_items").insert(items_to_insert).execute()

                    st.success(f"✅ 專案 {p_code} 建立成功！")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"寫入資料庫失敗: {e}")
                    if "duplicate key" in str(e):
                        st.error("⛔ 專案代號已存在，請檢查 Project Code。")

    # --- 專案列表檢視區 (依照憲法 4-3 總攬的前身) ---
    st.divider()
    st.subheader("📋 已建檔專案清單")
    
    # 這裡我們做一個簡單的 Join 查詢 (Supabase 語法)
    # select project_code, project_name, partners(name)
    res = supabase.table("projects").select("project_code, project_name, order_grade, start_date, partners(name)").execute()
    
    if res.data:
        # 整理資料
        clean_data = []
        for r in res.data:
            clean_data.append({
                "代號": r['project_code'],
                "名稱": r['project_name'],
                "客戶": r['partners']['name'] if r['partners'] else "未知",
                "等級": r['order_grade'],
                "開案日": r['start_date']
            })
        st.dataframe(pd.DataFrame(clean_data), use_container_width=True)
