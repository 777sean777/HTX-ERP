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

        res_orders = supabase.table("sales_orders").select("so_number").order("created_at", desc=True).execute()
        existing_orders = [o['so_number'] for o in res_orders.data]
    except Exception as e:
        st.error(f"資料讀取失敗: {e}")
        return

    # --- 2. 編輯/新增 切換 ---
    c_sel, c_btn = st.columns([3, 1])
    target_so = c_sel.selectbox("✏️ 選擇要編輯的訂單 (或選擇建立新訂單)", ["(建立新訂單)"] + existing_orders)

    # --- 3. 初始化 ---
    if "current_so_target" not in st.session_state:
        st.session_state.current_so_target = "(建立新訂單)"
        st.session_state.so_form_data = get_empty_form()

    if st.session_state.current_so_target != target_so:
        st.session_state.current_so_target = target_so
        if target_so == "(建立新訂單)":
            st.session_state.so_form_data = get_empty_form()
            st.toast("已切換至新訂單模式")
        else:
            load_order_data(supabase, target_so)
            st.toast(f"已載入訂單 {target_so}")

    form_data = st.session_state.so_form_data

    # --- 4. 表單區域 ---
    with st.container(border=True):
        st.subheader("📋 訂單詳細內容")
        
        with st.form("so_main_form"):
            # A. 表頭
            st.markdown("#### 1. 訂單表頭 (Header)")
            c1, c2 = st.columns(2)
            
            default_proj_idx = 0
            if form_data["project_code"]:
                for idx, opt in enumerate(proj_options):
                    if opt.startswith(form_data["project_code"]):
                        default_proj_idx = idx
                        break
            
            selected_proj_label = c1.selectbox("選擇專案", [""] + proj_options, index=default_proj_idx + 1 if form_data["project_code"] else 0)
            
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
            so_no = c3.text_input("訂單編號", value=form_data["so_no"], disabled=(target_so != "(建立新訂單)"))
            contract_no = c4.text_input("合約編號", value=form_data["contract_no"])
            
            try:
                if isinstance(form_data["order_date"], str):
                    def_date = datetime.strptime(form_data["order_date"], "%Y-%m-%d").date()
                else: def_date = form_data["order_date"]
            except: def_date = date.today()
            order_date = c5.date_input("訂單日期", value=def_date)
            
            tax_opts = ["含稅", "未稅", "零稅"]
            tax_idx = tax_opts.index(form_data["tax_type"]) if form_data["tax_type"] in tax_opts else 0
            tax_type = c6.selectbox("稅別", tax_opts, index=tax_idx)

            # B. 產品明細 (核心修改處)
            st.markdown("#### 2. 產品明細 (Line Items)")
            st.caption("請在下方輸入數量與單價，系統將自動計算小計。")
            
            # 使用 Data Editor 讓用戶輸入
            edited_items = st.data_editor(
                form_data["items"],
                num_rows="dynamic",
                use_container_width=True,
                key=f"editor_items_{target_so}",
                column_config={
                    "數量": st.column_config.NumberColumn(min_value=1, required=True),
                    "單價": st.column_config.NumberColumn(min_value=0, format="$%d", required=True)
                }
            )
            
            # ★★★ 即時運算邏輯 ★★★
            # 只要上面的 data_editor 有變動 (按 Enter)，程式會重跑，這裡就會重新計算
            header_total = 0
            display_df = pd.DataFrame()
            
            if not edited_items.empty:
                # 複製一份來做計算，以免汙染原始輸入
                calc_df = edited_items.copy()
                try:
                    # 強制轉型防呆
                    calc_df["數量"] = pd.to_numeric(calc_df["數量"], errors='coerce').fillna(0)
                    calc_df["單價"] = pd.to_numeric(calc_df["單價"], errors='coerce').fillna(0)
                    
                    # 計算小計
                    calc_df["金額 (小計)"] = calc_df["數量"] * calc_df["單價"]
                    
                    # 計算總額
                    header_total = calc_df["金額 (小計)"].sum()
                    
                    # 準備顯示用的表格 (加上小計欄位)
                    display_df = calc_df
                except:
                    pass

            # 顯示「試算結果表」 (這是唯讀的，讓用戶確認金額)
            if not display_df.empty:
                st.markdown("⬇️ **明細試算預覽 (自動計算)**")
                st.dataframe(
                    display_df, 
                    use_container_width=True,
                    column_config={
                        "金額 (小計)": st.column_config.NumberColumn(format="$%d", help="數量 * 單價")
                    }
                )

            # 顯示超大總金額
            st.metric("💰 訂單總金額 (Total Amount)", f"${header_total:,.0f}")

            # C. 收款計畫
            st.markdown("#### 3. 收款計畫 (Payment Schedule)")
            df_pay = form_data["payments"].copy()
            if not df_pay.empty and "預計收款日" in df_pay.columns:
                df_pay["預計收款日"] = pd.to_datetime(df_pay["預計收款日"]).dt.date

            edited_payments = st.data_editor(
                df_pay,
                num_rows="dynamic",
                use_container_width=True,
                key=f"editor_payments_{target_so}",
                column_config={
                    "預計收款日": st.column_config.DateColumn(format="YYYY-MM-DD", required=True),
                    "金額": st.column_config.NumberColumn(format="$%d", required=True)
                }
            )
            
            # 檢核邏輯
            payment_total = 0
            if not edited_payments.empty:
                try: payment_total = edited_payments["金額"].sum()
                except: pass
            
            diff = header_total - payment_total
            is_valid = (diff == 0) and (header_total > 0)
            
            if is_valid:
                st.success(f"✅ 金額檢核通過：收款總額 ${payment_total:,.0f} 與訂單總額相符。")
            else:
                if header_total == 0:
                    st.warning("⚠️ 請先輸入產品明細。")
                else:
                    st.error(f"❌ 金額不符！訂單總額 ${header_total:,.0f} vs 收款總額 ${payment_total:,.0f} (差額: ${diff:,.0f})")

            # D. 存檔
            btn_label = "💾 更新訂單" if target_so != "(建立新訂單)" else "💾 建立新訂單"
            submitted = st.form_submit_button(btn_label)

            if submitted:
                if not is_valid:
                    st.error("⛔ 無法存檔：請先修正金額差異！")
                elif not so_no or not p_code:
                    st.error("訂單編號與專案為必填")
                else:
                    # 存檔時使用有小計的 items 邏輯嗎？不，資料庫通常不存小計 (冗餘欄位)，只存單價數量
                    save_order(supabase, so_no, p_code, cust_id, contract_no, order_date, tax_type, edited_items, edited_payments)

    # --- 5. 列表 ---
    st.divider()
    if target_so == "(建立新訂單)":
        st.subheader("📋 所有訂單列表")
        render_order_list(supabase)

# === Helpers ===
def get_empty_form():
    return {
        "so_no": "", "project_code": "", "contract_no": "", "order_date": date.today(), "tax_type": "含稅",
        "items": pd.DataFrame([{"品項名稱": "", "規格": "", "數量": 1, "單價": 0}]),
        "payments": pd.DataFrame([{"期數名稱": "訂金", "預計收款日": date.today(), "金額": 0}])
    }

def load_order_data(supabase, so_no):
    try:
        head = supabase.table("sales_orders").select("*").eq("so_number", so_no).single().execute().data
        items = supabase.table("so_items").select("product_name, spec, quantity, unit_price").eq("so_number", so_no).execute().data
        df_items = pd.DataFrame(items) if items else pd.DataFrame([{"品項名稱": "", "規格": "", "數量": 1, "單價": 0}])
        df_items = df_items.rename(columns={"product_name": "品項名稱", "spec": "規格", "quantity": "數量", "unit_price": "單價"})
        pays = supabase.table("so_payments").select("term_name, expected_date, amount").eq("so_number", so_no).execute().data
        df_pays = pd.DataFrame(pays) if pays else pd.DataFrame([{"期數名稱": "", "預計收款日": date.today(), "金額": 0}])
        df_pays = df_pays.rename(columns={"term_name": "期數名稱", "expected_date": "預計收款日", "amount": "金額"})
        if not df_pays.empty and "預計收款日" in df_pays.columns:
            df_pays["預計收款日"] = pd.to_datetime(df_pays["預計收款日"]).dt.date

        st.session_state.so_form_data = {
            "so_no": head["so_number"], "project_code": head["project_code"], "contract_no": head["contract_no"],
            "order_date": head["order_date"], "tax_type": head["tax_type"], "items": df_items, "payments": df_pays
        }
    except Exception as e: st.error(f"載入失敗: {e}")

def save_order(supabase, so_no, p_code, cust_id, contract_no, order_date, tax_type, items_df, pays_df):
    try:
        final_total = 0
        items_data = []
        if not items_df.empty:
            for _, row in items_df.iterrows():
                if row.get("品項名稱"):
                    qty = float(row.get("數量", 0))
                    price = float(row.get("單價", 0))
                    amt = qty * price
                    final_total += amt
                    items_data.append({
                        "so_number": so_no, "product_name": row["品項名稱"], "spec": row.get("規格", ""),
                        "quantity": qty, "unit_price": price, "amount": amt
                    })

        payments_data = []
        if not pays_df.empty:
            for _, row in pays_df.iterrows():
                if row.get("金額", 0) > 0:
                    payments_data.append({
                        "so_number": so_no, "term_name": row.get("期數名稱", ""),
                        "expected_date": str(row["預計收款日"]), "amount": float(row["金額"])
                    })

        so_header = {
            "so_number": so_no, "project_code": p_code, "cust_id": cust_id,
            "contract_no": contract_no, "order_date": str(order_date),
            "tax_type": tax_type, "total_amount": final_total, "status": "Confirmed"
        }
        supabase.table("sales_orders").upsert(so_header).execute()
        supabase.table("so_items").delete().eq("so_number", so_no).execute()
        if items_data: supabase.table("so_items").insert(items_data).execute()
        supabase.table("so_payments").delete().eq("so_number", so_no).execute()
        if payments_data: supabase.table("so_payments").insert(payments_data).execute()

        sync_matrix(supabase, p_code)

        st.success(f"✅ 訂單 {so_no} 儲存成功！")
        st.session_state.current_so_target = "(建立新訂單)"
        st.session_state.so_form_data = get_empty_form()
        time.sleep(1)
        st.rerun()
    except Exception as e: st.error(f"存檔失敗: {e}")

def sync_matrix(supabase, p_code):
    all_payments = supabase.table("so_payments").select("expected_date, amount, sales_orders!inner(project_code)").eq("sales_orders.project_code", p_code).execute()
    monthly_revenue = {}
    if all_payments.data:
        for p in all_payments.data:
            d_obj = datetime.strptime(p['expected_date'], "%Y-%m-%d")
            month_key = d_obj.replace(day=1).strftime("%Y-%m-%d")
            monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + p['amount']
    
    for m_key, amt in monthly_revenue.items():
        exist = supabase.table("project_matrix").select("plan_amount").eq("project_code", p_code).eq("year_month", m_key).eq("cost_item", "2.1 產品銷售收入").execute()
        current_plan = exist.data[0]['plan_amount'] if exist.data else 0
        supabase.table("project_matrix").upsert(
            {"project_code": p_code, "year_month": m_key, "cost_item": "2.1 產品銷售收入", "plan_amount": current_plan, "real_amount": amt},
            on_conflict="project_code, year_month, cost_item"
        ).execute()

def render_order_list(supabase):
    try:
        res_so = supabase.table("sales_orders").select("so_number, order_date, total_amount, status, project_code, partners(name)").order("order_date", desc=True).execute()
        if res_so.data:
            for so in res_so.data:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                    c1.markdown(f"**{so['so_number']}**")
                    cust = so['partners']['name'] if so['partners'] else "Unknown"
                    c1.caption(f"{so['project_code']} | {cust}")
                    c2.markdown(f"${so['total_amount']:,.0f}")
                    c3.write(so['status'])
                    if c4.button("🗑️", key=f"del_{so['so_number']}"):
                        supabase.table("sales_orders").delete().eq("so_number", so['so_number']).execute()
                        sync_matrix(supabase, so['project_code']) 
                        st.toast("已刪除")
                        time.sleep(1)
                        st.rerun()
        else: st.info("尚無訂單")
    except: pass
