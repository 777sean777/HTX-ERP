import streamlit as st
import pandas as pd
import time
from datetime import datetime, date

def show(supabase):
    st.markdown('<p class="main-header">📝 銷售訂單管理 (Sales Order)</p>', unsafe_allow_html=True)

    # --- 1. 準備資料 ---
    # 抓取所有專案 (用於下拉選單)
    try:
        res_proj = supabase.table("projects").select("project_code, project_name, cust_id, partners(name)").execute()
        # 建立 專案代號 -> 專案物件 的對映
        proj_map = {p['project_code']: p for p in res_proj.data}
        proj_options = [f"{p['project_code']} | {p['project_name']}" for p in res_proj.data]
    except:
        st.error("無法讀取專案資料")
        return

    # --- 2. 訂單輸入表單 ---
    with st.expander("➕ 新增銷售訂單 (SO)", expanded=True):
        with st.form("so_form"):
            # A. 表頭資料
            st.markdown("#### 1. 訂單表頭 (Header)")
            c1, c2 = st.columns(2)
            
            # 專案選擇邏輯
            selected_proj_label = c1.selectbox("選擇專案", [""] + proj_options)
            
            # 自動帶入客戶 (唯讀)
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
            so_no = c3.text_input("訂單編號 (SO No.)", placeholder="例如: SO-20260101")
            contract_no = c4.text_input("合約編號")
            order_date = c5.date_input("訂單日期")
            tax_type = c6.selectbox("稅別", ["含稅", "未稅", "零稅"])

            # B. 產品明細 (動態)
            st.markdown("#### 2. 產品明細 (Line Items)")
            # 預設一行空資料
            default_items = pd.DataFrame([{"品項名稱": "", "規格": "", "數量": 1, "單價": 0}])
            
            edited_items = st.data_editor(
                default_items,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "數量": st.column_config.NumberColumn(min_value=1),
                    "單價": st.column_config.NumberColumn(min_value=0, format="$%d")
                }
            )
            
            # 即時計算訂單總額
            # 注意：這裡只能算個大概給使用者看，實際存檔會重算
            temp_total = 0
            if not edited_items.empty:
                edited_items["小計"] = edited_items["數量"] * edited_items["單價"]
                temp_total = edited_items["小計"].sum()
            
            st.caption(f"試算總金額: ${temp_total:,.0f}")

            # C. 收款計畫 (Payment Schedule)
            st.markdown("#### 3. 收款計畫 (Payment Schedule)")
            st.info("💡 此處的「預計收款月份」將自動寫入專案矩陣的【實際收入 (Real)】欄位。")
            
            default_payments = pd.DataFrame([
                {"期數名稱": "訂金 30%", "預計收款日": date.today(), "金額": int(temp_total * 0.3)},
                {"期數名稱": "尾款 70%", "預計收款日": date.today(), "金額": int(temp_total * 0.7)}
            ])
            
            edited_payments = st.data_editor(
                default_payments,
                num_rows="dynamic",
                use_container_width=True,
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
                        # 1. 計算最終總金額
                        final_total = 0
                        items_data = []
                        if not edited_items.empty:
                            for _, row in edited_items.iterrows():
                                if row["品項名稱"]:
                                    qty = float(row["數量"])
                                    price = float(row["單價"])
                                    amt = qty * price
                                    final_total += amt
                                    items_data.append({
                                        "so_number": so_no,
                                        "product_name": row["品項名稱"],
                                        "spec": row["規格"],
                                        "quantity": qty,
                                        "unit_price": price,
                                        "amount": amt
                                    })

                        # 2. 準備收款計畫資料
                        payments_data = []
                        if not edited_payments.empty:
                            for _, row in edited_payments.iterrows():
                                if row["金額"] > 0:
                                    payments_data.append({
                                        "so_number": so_no,
                                        "term_name": row["期數名稱"],
                                        "expected_date": str(row["預計收款日"]),
                                        "amount": float(row["金額"])
                                    })

                        # 3. 寫入 Sales Order Header
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

                        # 4. 寫入 Items (先刪後加)
                        supabase.table("so_items").delete().eq("so_number", so_no).execute()
                        if items_data:
                            supabase.table("so_items").insert(items_data).execute()

                        # 5. 寫入 Payments (先刪後加)
                        supabase.table("so_payments").delete().eq("so_number", so_no).execute()
                        if payments_data:
                            supabase.table("so_payments").insert(payments_data).execute()

                        # 6. ★★★ 觸發矩陣連動 (Sync to Matrix Real) ★★★
                        # 邏輯：重新計算該專案所有 SO Payment 的總和，並更新到 Project Matrix
                        # 這裡我們做一個簡化的版本：直接把這筆 SO 的 Payment 加進去
                        # 更嚴謹的做法應該是 SQL Trigger 或由後端統一計算，但在 Streamlit 層：
                        
                        # 6.1 讀取目前專案的所有 SO Payments (包含剛剛存進去的)
                        # 這是一個「全域重算」邏輯，確保數據一致性
                        all_payments = supabase.table("so_payments")\
                            .select("expected_date, amount, sales_orders!inner(project_code)")\
                            .eq("sales_orders.project_code", p_code)\
                            .execute()
                        
                        # 6.2 依月份加總
                        monthly_revenue = {}
                        if all_payments.data:
                            for p in all_payments.data:
                                # 轉成當月 1 號
                                d_obj = datetime.strptime(p['expected_date'], "%Y-%m-%d")
                                month_key = d_obj.replace(day=1).strftime("%Y-%m-%d")
                                monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + p['amount']
                        
                        # 6.3 寫入 Project Matrix (Real Column)
                        # 科目固定為 "2.1 產品銷售收入" (依據憲法)
                        matrix_upserts = []
                        for m_key, amt in monthly_revenue.items():
                            matrix_upserts.append({
                                "project_code": p_code,
                                "year_month": m_key,
                                "cost_item": "2.1 產品銷售收入",
                                "real_amount": amt
                                # 注意：這裡只更新 real_amount，plan_amount 不會被覆蓋 (Supabase upsert 特性)
                                # 但為了安全，最好是資料庫層級處理。這裡假設 upsert 會 merge。
                                # 如果 upsert 會清空沒傳的欄位，則需要先讀再寫。
                                # 由於 project_matrix 有 UNIQUE index，這裡的 Upsert 其實是 Replace。
                                # 為了不掉 Plan 數據，我們先讀該月的 Plan
                            })
                        
                        # 6.4 安全寫入邏輯：先讀 -> 合併 -> 寫回
                        for up in matrix_upserts:
                            # 查現有 Plan
                            exist = supabase.table("project_matrix").select("plan_amount")\
                                .eq("project_code", p_code)\
                                .eq("year_month", up["year_month"])\
                                .eq("cost_item", up["cost_item"])\
                                .execute()
                            
                            current_plan = exist.data[0]['plan_amount'] if exist.data else 0
                            
                            # 合併數據
                            final_record = {
                                "project_code": p_code,
                                "year_month": up["year_month"],
                                "cost_item": up["cost_item"],
                                "plan_amount": current_plan, # 保持原 Plan 不變
                                "real_amount": up["real_amount"] # 更新 Real
                            }
                            supabase.table("project_matrix").upsert(final_record).execute()

                        st.success(f"✅ 訂單 {so_no} 已成立，並同步更新財務矩陣實際收入！")
                        time.sleep(1)
                        st.rerun()

                    except Exception as e:
                        st.error(f"存檔失敗: {e}")

    # --- 3. 訂單列表 ---
    st.divider()
    st.subheader("📋 訂單列表 (Sales Orders)")
    
    try:
        # 關聯查詢：訂單 -> 專案 -> 客戶
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
                    
                    # 刪除功能
                    if c4.button("🗑️", key=f"del_so_{so['so_number']}"):
                        supabase.table("sales_orders").delete().eq("so_number", so['so_number']).execute()
                        st.toast("訂單已刪除")
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("尚無訂單資料")

    except Exception as e:
        st.error(f"讀取列表失敗: {e}")
