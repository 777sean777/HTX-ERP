import streamlit as st
import pandas as pd
import time
from datetime import datetime, date

def show(supabase):
    st.markdown('<p class="main-header">📝 銷售訂單管理 (Sales Order)</p>', unsafe_allow_html=True)

    # --- 1. 準備資料 ---
    try:
        res_proj = supabase.table("projects").select("project_code, project_name, cust_id, partners(name)").execute()
        proj_map = {p['project_code']: p for p in res_proj.data}
        proj_options = [f"{p['project_code']} | {p['project_name']}" for p in res_proj.data]
    except:
        st.error("無法讀取專案資料")
        return

    # --- 2. 初始化 Session State (避開名稱衝突) ---
    # ★★★ 修正點：改名為 so_form_data，避免跟 st.form("so_form") 撞名 ★★★
    if "so_form_data" not in st.session_state:
        st.session_state.so_form_data = {
            "so_no": "",
            "contract_no": "",
            "items": pd.DataFrame([{"品項名稱": "", "規格": "", "數量": 1, "單價": 0}]),
            "payments": pd.DataFrame([
                {"期數名稱": "訂金 30%", "預計收款日": date.today(), "金額": 0},
                {"期數名稱": "尾款 70%", "預計收款日": date.today(), "金額": 0}
            ])
        }

    # --- 憲法第貳條：Dev Mode 一鍵填充 ---
    if st.session_state.get("dev_mode", False):
        with st.sidebar:
            st.markdown("### 🛠️ SO 開發工具")
            if st.button("🚀 填入測試訂單 (Test Data)"):
                # 模擬一筆 100 萬的訂單
                mock_items = pd.DataFrame([
                    {"品項名稱": "高機能透氣布料-A級", "規格": "Roll-200M", "數量": 100, "單價": 5000},
                    {"品項名稱": "防水塗層加工", "規格": "Batch-01", "數量": 100, "單價": 1000}
                ])
                # 總額 600,000
                mock_payments = pd.DataFrame([
                    {"期數名稱": "訂金 30%", "預計收款日": date(2026, 2, 15), "金額": 180000},
                    {"期數名稱": "出貨款 60%", "預計收款日": date(2026, 3, 15), "金額": 360000},
                    {"期數名稱": "驗收尾款 10%", "預計收款日": date(2026, 4, 15), "金額": 60000}
                ])
                
                # 更新 State
                st.session_state.so_form_data = {
                    "so_no": "SO-20260115-001",
                    "contract_no": "CT-2026-A01",
                    "items": mock_items,
                    "payments": mock_payments
                }
                st.toast("✅ 測試數據已填入！")
                time.sleep(0.5)
                st.rerun()

    # 讀取當前資料
    form_data = st.session_state.so_form_data

    # --- 3. 訂單輸入表單 ---
    with st.expander("➕ 新增銷售訂單 (SO)", expanded=True):
        # ★★★ 這裡 form 的 key 維持 "so_main_form" ★★★
        with st.form("so_main_form"):
            # A. 表頭資料
            st.markdown("#### 1. 訂單表頭 (Header)")
            c1, c2 = st.columns(2)
            
            selected_proj_label = c1.selectbox("選擇專案", [""] + proj_options)
            
            cust_display = ""
            p_code = ""
            cust_id = None
            
            if selected_proj_label:
                p_code = selected_proj_label.split(" | ")[0]
                proj_data = proj_map.get(p_code)
                if proj_data and proj_data.get('partners'):
                    cust_display = proj_data['partners']['name']
                    cust_id = proj_data['cust_id']
            
            c2.text_input("客戶 (自動帶入)", value=cust_display, disabled=True)

            c3, c4, c5, c6 = st.columns(4)
            so_no = c3.text_input("訂單編號", value=form_data["so_no"])
            contract_no = c4.text_input("合約編號", value=form_data["contract_no"])
            order_date = c5.date_input("訂單日期")
            tax_type = c6.selectbox("稅別", ["含稅", "未稅", "零稅"])

            # B. 產品明細 (動態)
            st.markdown("#### 2. 產品明細 (Line Items)")
            edited_items = st.data_editor(
                form_data["items"],
                num_rows="dynamic",
                use_container_width=True,
                key="editor_items", # 加上 key 避免重繪丟失
                column_config={
                    "數量": st.column_config.NumberColumn(min_value=1),
                    "單價": st.column_config.NumberColumn(min_value=0, format="$%d")
                }
            )
            
            # 即時計算訂單總額
            temp_total = 0
            if not edited_items.empty:
                try:
                    edited_items["小計"] = edited_items["數量"].astype(float) * edited_items["單價"].astype(float)
                    temp_total = edited_items["小計"].sum()
                except: pass
            
            st.caption(f"試算總金額: ${temp_total:,.0f}")

            # C. 收款計畫 (Payment Schedule)
            st.markdown("#### 3. 收款計畫 (Payment Schedule)")
            st.info("💡 此處的「預計收款月份」將自動寫入專案矩陣的【實際收入 (Real)】欄位。")
            
            edited_payments = st.data_editor(
                form_data["payments"],
                num_rows="dynamic",
                use_container_width=True,
                key="editor_payments", # 加上 key
                column_config={
                    "預計收款日": st.column_config.DateColumn(format="YYYY-MM-DD", required=True),
                    "金額": st.column_config.NumberColumn(format="$%d", required=True)
                }
            )

            # D. 存檔按鈕
            submitted = st.form_submit_button("💾 簽核並儲存訂單")

            if submitted:
                if not so_no or not p_code:
                    st.error("❌ 訂單編號與專案代號為必填！")
                else:
                    try:
                        # 1. 準備數據
                        final_total = 0
                        items_data = []
                        if not edited_items.empty:
                            for _, row in edited_items.iterrows():
                                if row.get("品項名稱"):
                                    qty = float(row.get("數量", 0))
                                    price = float(row.get("單價", 0))
                                    amt = qty * price
                                    final_total += amt
                                    items_data.append({
                                        "so_number": so_no,
                                        "product_name": row["品項名稱"],
                                        "spec": row.get("規格", ""),
                                        "quantity": qty,
                                        "unit_price": price,
                                        "amount": amt
                                    })

                        payments_data = []
                        if not edited_payments.empty:
                            for _, row in edited_payments.iterrows():
                                if row.get("金額", 0) > 0:
                                    payments_data.append({
                                        "so_number": so_no,
                                        "term_name": row.get("期數名稱", ""),
                                        "expected_date": str(row["預計收款日"]),
                                        "amount": float(row["金額"])
                                    })

                        # 2. 寫入 DB
                        so_header = {
                            "so_number": so_no,
                            "project_code": p_code,
                            "cust_id": cust_id,
                            "contract_no": contract_no,
                            "order_date": str(order_date),
                            "tax_type": tax_type,
                            "total_amount": final_total,
                            "status": "Confirmed"
                        }
                        supabase.table("sales_orders").upsert(so_header).execute()

                        supabase.table("so_items").delete().eq("so_number", so_no).execute()
                        if items_data: supabase.table("so_items").insert(items_data).execute()

                        supabase.table("so_payments").delete().eq("so_number", so_no).execute()
                        if payments_data: supabase.table("so_payments").insert(payments_data).execute()

                        # 3. 連動矩陣 (Sync Matrix)
                        all_payments = supabase.table("so_payments")\
                            .select("expected_date, amount, sales_orders!inner(project_code)")\
                            .eq("sales_orders.project_code", p_code)\
                            .execute()
                        
                        monthly_revenue = {}
                        if all_payments.data:
                            for p in all_payments.data:
                                d_obj = datetime.strptime(p['expected_date'], "%Y-%m-%d")
                                month_key = d_obj.replace(day=1).strftime("%Y-%m-%d")
                                monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + p['amount']
                        
                        for m_key, amt in monthly_revenue.items():
                            exist = supabase.table("project_matrix").select("plan_amount")\
                                .eq("project_code", p_code)\
                                .eq("year_month", m_key)\
                                .eq("cost_item", "2.1 產品銷售收入")\
                                .execute()
                            current_plan = exist.data[0]['plan_amount'] if exist.data else 0
                            
                            supabase.table("project_matrix").upsert({
                                "project_code": p_code,
                                "year_month": m_key,
                                "cost_item": "2.1 產品銷售收入",
                                "plan_amount": current_plan,
                                "real_amount": amt
                            }).execute()

                        st.success(f"✅ 訂單 {so_no} 已成立，並同步更新財務矩陣！")
                        # 清空 Session State
                        del st.session_state.so_form_data
                        time.sleep(1)
                        st.rerun()

                    except Exception as e:
                        st.error(f"存檔失敗: {e}")

    # --- 4. 訂單列表 ---
    st.divider()
    st.subheader("📋 訂單列表 (Sales Orders)")
    try:
        res_so = supabase.table("sales_orders").select("so_number, order_date, total_amount, status, project_code, partners(name)").order("order_date", desc=True).execute()
        if res_so.data:
            for so in res_so.data:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                    c1.markdown(f"**{so['so_number']}**")
                    cust_name = so['partners']['name'] if so['partners'] else "Unknown"
                    c1.caption(f"{so['project_code']} | {cust_name}")
                    c2.markdown(f"總額: **${so['total_amount']:,.0f}**")
                    c3.write(f"狀態: {so['status']}")
                    
                    if c4.button("🗑️", key=f"del_{so['so_number']}"):
                        supabase.table("sales_orders").delete().eq("so_number", so['so_number']).execute()
                        st.toast("已刪除")
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("尚無訂單資料")
    except: pass
