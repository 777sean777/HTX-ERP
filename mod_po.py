import streamlit as st
import pandas as pd
import time
import io
from datetime import datetime, date

# --- 憲法 3.x 變動費用科目 ---
COST_ITEMS = [
    "3.1 原料採購成本", "3.1 輔料採購成本", "3.1 機械結構件採購", "3.1 電控零件採購", "3.1 耗材成本",
    "3.3 委外加工費用", "3.3 打樣及設計費", "3.3 運輸與倉儲",
    "3.5 新布料開發與打樣", "3.5 測試材料費",
    "3.7 廣告宣傳費", "3.7 差旅費"
]

def show(supabase):
    st.markdown('<p class="main-header">🛒 採購訂單管理 (Purchase Order)</p>', unsafe_allow_html=True)

    # --- 1. 準備資料 ---
    try:
        # 專案
        res_proj = supabase.table("projects").select("project_code, project_name").execute()
        proj_options = [f"{p['project_code']} | {p['project_name']}" for p in res_proj.data]
        
        # 供應商
        res_supp = supabase.table("partners").select("id, name, credit_limit, company_address, company_phone, contact_person").eq("type", "Supplier").execute()
        supp_map = {s['name']: s for s in res_supp.data}
        supp_options = list(supp_map.keys())

        # 現有 PO
        res_po = supabase.table("purchase_orders").select("po_number").order("created_at", desc=True).execute()
        existing_pos = [p['po_number'] for p in res_po.data]
    except:
        st.error("資料讀取失敗")
        return

    # --- 2. 編輯/新增 切換 ---
    c_sel, _ = st.columns([3, 1])
    target_po = c_sel.selectbox("✏️ 選擇要編輯的採購單 (或建立新單)", ["(建立新採購單)"] + existing_pos)

    if "current_po_target" not in st.session_state:
        st.session_state.current_po_target = "(建立新採購單)"
        st.session_state.po_form_data = get_empty_form()

    if st.session_state.current_po_target != target_po:
        st.session_state.current_po_target = target_po
        if target_po == "(建立新採購單)":
            st.session_state.po_form_data = get_empty_form()
            st.toast("已切換至新單模式")
        else:
            load_po_data(supabase, target_po)
            st.toast(f"已載入 {target_po}")

    # Dev Mode Fill
    if st.session_state.get("dev_mode", False):
        with st.sidebar:
            st.markdown("### 🛠️ PO 開發工具")
            if st.button("🚀 填入測試採購"):
                mock_items = pd.DataFrame([
                    {"品項": "PP塑膠粒-T500", "規格": "25kg/包", "數量": 200, "單價": 450},
                    {"品項": "色母-黑色", "規格": "1kg/罐", "數量": 10, "單價": 1000}
                ])
                mock_pays = pd.DataFrame([{"期數": "月結60天", "預計付款日": date(2026, 3, 31), "金額": 100000}])
                st.session_state.po_form_data = {
                    "po_no": "PO-20260115-001", "project_code": "", "supplier_name": supp_options[0] if supp_options else "",
                    "cost_item": "3.1 原料採購成本", "order_date": date.today(), "tax_type": "含稅",
                    "items": mock_items, "payments": mock_pays
                }
                st.rerun()

    form_data = st.session_state.po_form_data

    # --- 3. 採購表單 (Input Area) ---
    with st.container(border=True):
        st.subheader("📋 採購單輸入 (Input)")
        with st.form("po_main_form"):
            # A. 表頭
            st.markdown("#### 1. 採購表頭")
            c1, c2 = st.columns(2)
            
            def_proj_idx = 0
            if form_data["project_code"]:
                for i, opt in enumerate(proj_options):
                    if opt.startswith(form_data["project_code"]):
                        def_proj_idx = i
                        break
            sel_proj = c1.selectbox("歸屬專案", [""] + proj_options, index=def_proj_idx + 1 if form_data["project_code"] else 0)
            
            def_supp_idx = 0
            if form_data["supplier_name"] in supp_options:
                def_supp_idx = supp_options.index(form_data["supplier_name"])
            sel_supp = c2.selectbox("供應商", supp_options, index=def_supp_idx)

            supp_limit = 0
            if sel_supp:
                supp_limit = supp_map[sel_supp]['credit_limit']
                c2.caption(f"ℹ️ 額度上限: ${supp_limit:,.0f}")

            c3, c4, c5, c6 = st.columns(4)
            po_no = c3.text_input("採購單號", value=form_data["po_no"], disabled=(target_po != "(建立新採購單)"))
            
            def_cost_idx = 0
            if form_data["cost_item"] in COST_ITEMS: def_cost_idx = COST_ITEMS.index(form_data["cost_item"])
            cost_item = c4.selectbox("歸屬科目", COST_ITEMS, index=def_cost_idx)
            
            try:
                if isinstance(form_data["order_date"], str): order_d = datetime.strptime(form_data["order_date"], "%Y-%m-%d").date()
                else: order_d = form_data["order_date"]
            except: order_d = date.today()
            order_date = c5.date_input("採購日期", value=order_d)
            tax_type = c6.selectbox("稅別", ["含稅", "未稅"], index=0 if form_data["tax_type"] == "含稅" else 1)

            # B. 明細 (移除冗餘表格，只留編輯器)
            st.markdown("#### 2. 採購明細")
            st.caption("請直接輸入數量與單價，總計將於下方自動計算。")
            
            edited_items = st.data_editor(
                form_data["items"], num_rows="dynamic", use_container_width=True, key=f"po_items_{target_po}",
                column_config={
                    "數量": st.column_config.NumberColumn(min_value=1, required=True), 
                    "單價": st.column_config.NumberColumn(min_value=0, required=True, format="$%d")
                }
            )
            
            # --- 即時稅務計算 (Tax Calculation) ---
            raw_total = 0.0
            tax_amount = 0.0
            final_total = 0.0
            
            if not edited_items.empty:
                try:
                    # 計算每一行的小計
                    subtotals = edited_items["數量"].astype(float) * edited_items["單價"].astype(float)
                    sum_val = subtotals.sum()
                    
                    if tax_type == "含稅":
                        final_total = sum_val
                        raw_total = sum_val / 1.05
                        tax_amount = final_total - raw_total
                    else: # 未稅
                        raw_total = sum_val
                        tax_amount = raw_total * 0.05
                        final_total = raw_total + tax_amount
                except: pass

            # 顯示計算結果 (大字報)
            # 我們不再顯示那個重複的表格，改用 Metrics
            st.markdown("---")
            k1, k2, k3 = st.columns(3)
            k1.metric("銷售額 (未稅)", f"${raw_total:,.0f}")
            k2.metric("營業稅 (5%)", f"${tax_amount:,.0f}")
            k3.metric("總計 (含稅)", f"${final_total:,.0f}", delta="本單應付總額")

            # C. 付款計畫
            st.markdown("#### 3. 付款計畫")
            df_pay = form_data["payments"].copy()
            if not df_pay.empty and "預計付款日" in df_pay.columns:
                df_pay["預計付款日"] = pd.to_datetime(df_pay["預計付款日"]).dt.date
            
            edited_payments = st.data_editor(
                df_pay, num_rows="dynamic", use_container_width=True, key=f"po_pay_{target_po}",
                column_config={"預計付款日": st.column_config.DateColumn(format="YYYY-MM-DD", required=True), "金額": st.column_config.NumberColumn(required=True)}
            )
            
            pay_total = edited_payments["金額"].sum() if not edited_payments.empty else 0
            diff = final_total - pay_total
            
            # D. 檢核
            is_valid = True
            
            if abs(diff) < 1 and final_total > 0: # 允許 1 元誤差
                st.success(f"✅ 金額相符")
            else:
                is_valid = False
                if final_total == 0: st.warning("⚠️ 請輸入明細")
                else: st.error(f"❌ 付款總額不符！差額: ${diff:,.0f}")

            if sel_supp and supp_limit > 0 and final_total > supp_limit:
                is_valid = False
                st.error(f"⛔ 超過額度上限 ${supp_limit:,.0f}！")

            # E. 存檔
            btn_txt = "💾 更新採購單" if target_po != "(建立新採購單)" else "💾 建立採購單"
            submitted = st.form_submit_button(btn_txt)
            
            if submitted:
                if not is_valid: st.error("無法存檔，請修正錯誤。")
                elif not po_no or not sel_proj: st.error("必填欄位缺漏")
                else:
                    p_code = sel_proj.split(" | ")[0]
                    supp_id = supp_map[sel_supp]['id']
                    save_po(supabase, po_no, p_code, supp_id, cost_item, order_date, tax_type, final_total, edited_items, edited_payments)

    # --- 4. 輸出與列表 (Output Area) ---
    st.divider()
    
    # 只有在「編輯模式」下才顯示匯出按鈕，確保資料已存檔
    if target_po != "(建立新採購單)":
        st.subheader("🖨️ 輸出正式文件")
        
        # 準備 Excel 數據
        # 重新讀取一次確保是最新的
        po_data_for_export = load_po_data_raw(supabase, target_po) 
        
        if po_data_for_export:
            # 產生 Excel
            excel_data = generate_excel_po(po_data_for_export, supp_map.get(po_data_for_export['supplier_name'], {}))
            
            c_dl, _ = st.columns([1, 4])
            c_dl.download_button(
                label=f"📥 下載正式採購單 ({target_po}).xlsx",
                data=excel_data,
                file_name=f"{target_po}_PurchaseOrder.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        render_po_list(supabase)

# === Helpers ===
def get_empty_form():
    return {
        "po_no": "", "project_code": "", "supplier_name": "", "cost_item": "3.1 原料採購成本",
        "order_date": date.today(), "tax_type": "含稅",
        "items": pd.DataFrame([{"品項": "", "規格": "", "數量": 1, "單價": 0}]),
        "payments": pd.DataFrame([{"期數": "月結", "預計付款日": date.today(), "金額": 0}])
    }

# 這是原本的 load，用來填 form
def load_po_data(supabase, po_no):
    try:
        head = supabase.table("purchase_orders").select("*, partners(name)").eq("po_number", po_no).single().execute().data
        items = supabase.table("po_items").select("product_name, spec, quantity, unit_price").eq("po_number", po_no).execute().data
        pays = supabase.table("po_payments").select("term_name, expected_date, amount").eq("po_number", po_no).execute().data
        
        df_items = pd.DataFrame(items).rename(columns={"product_name": "品項", "spec": "規格", "quantity": "數量", "unit_price": "單價"})
        df_pays = pd.DataFrame(pays).rename(columns={"term_name": "期數", "expected_date": "預計付款日", "amount": "金額"})
        if not df_pays.empty: df_pays["預計付款日"] = pd.to_datetime(df_pays["預計付款日"]).dt.date

        st.session_state.po_form_data = {
            "po_no": head["po_number"], "project_code": head["project_code"], 
            "supplier_name": head["partners"]["name"], "cost_item": head["cost_item"],
            "order_date": datetime.strptime(head["order_date"], "%Y-%m-%d").date(),
            "tax_type": head["tax_type"], "items": df_items, "payments": df_pays
        }
    except: st.error("載入失敗")

# 這是給 Export 用的，回傳原始資料結構
def load_po_data_raw(supabase, po_no):
    try:
        head = supabase.table("purchase_orders").select("*, partners(name)").eq("po_number", po_no).single().execute().data
        items = supabase.table("po_items").select("product_name, spec, quantity, unit_price").eq("po_number", po_no).execute().data
        head['items'] = items
        return head
    except: return None

def save_po(supabase, po_no, p_code, supp_id, cost_item, order_date, tax_type, total, items_df, pay_df):
    try:
        supabase.table("purchase_orders").upsert({
            "po_number": po_no, "project_code": p_code, "supplier_id": supp_id, "cost_item": cost_item,
            "order_date": str(order_date), "tax_type": tax_type, "total_amount": total, "status": "Confirmed"
        }).execute()
        
        supabase.table("po_items").delete().eq("po_number", po_no).execute()
        items_data = []
        for _, r in items_df.iterrows():
            if r.get("品項"):
                amt = float(r["數量"]) * float(r["單價"])
                items_data.append({"po_number": po_no, "product_name": r["品項"], "spec": r.get("規格"), "quantity": r["數量"], "unit_price": r["單價"], "amount": amt})
        if items_data: supabase.table("po_items").insert(items_data).execute()

        supabase.table("po_payments").delete().eq("po_number", po_no).execute()
        pay_data = []
        for _, r in pay_df.iterrows():
            if r["金額"] > 0:
                pay_data.append({"po_number": po_no, "term_name": r.get("期數"), "expected_date": str(r["預計付款日"]), "amount": float(r["金額"])})
        if pay_data: supabase.table("po_payments").insert(pay_data).execute()

        sync_po_matrix(supabase, p_code, cost_item)
        st.success("✅ 儲存成功！")
        # 這裡不重置 form，方便使用者直接按匯出
        time.sleep(1)
        st.rerun()
    except Exception as e: st.error(f"存檔失敗: {e}")

def sync_po_matrix(supabase, p_code, cost_item):
    res = supabase.table("po_payments").select("expected_date, amount, purchase_orders!inner(project_code, cost_item)").eq("purchase_orders.project_code", p_code).eq("purchase_orders.cost_item", cost_item).execute()
    monthly_cost = {}
    if res.data:
        for row in res.data:
            d = datetime.strptime(row['expected_date'], "%Y-%m-%d")
            m_key = d.replace(day=1).strftime("%Y-%m-%d")
            monthly_cost[m_key] = monthly_cost.get(m_key, 0) + row['amount']
    for m, amt in monthly_cost.items():
        exist = supabase.table("project_matrix").select("plan_amount").eq("project_code", p_code).eq("year_month", m).eq("cost_item", cost_item).execute()
        plan = exist.data[0]['plan_amount'] if exist.data else 0
        supabase.table("project_matrix").upsert(
            {"project_code": p_code, "year_month": m, "cost_item": cost_item, "plan_amount": plan, "real_amount": amt},
            on_conflict="project_code, year_month, cost_item"
        ).execute()

def render_po_list(supabase):
    try:
        res = supabase.table("purchase_orders").select("po_number, total_amount, partners(name), project_code").order("created_at", desc=True).execute()
        if res.data:
            st.subheader("📋 採購列表")
            for r in res.data:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 2, 1])
                    c1.markdown(f"**{r['po_number']}**")
                    c1.caption(f"{r['partners']['name']} | {r['project_code']}")
                    c2.markdown(f"${r['total_amount']:,.0f}")
                    if c3.button("🗑️", key=f"del_{r['po_number']}"):
                        supabase.table("purchase_orders").delete().eq("po_number", r['po_number']).execute()
                        st.toast("已刪除")
                        time.sleep(1)
                        st.rerun()
    except: pass

# --- Excel Generator ---
def generate_excel_po(po_data, supp_data):
    output = io.BytesIO()
    workbook = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # 建立 DataFrame 只是為了簡單轉 Excel，主要排版靠 xlsxwriter
    df = pd.DataFrame(po_data['items'])
    df = df.rename(columns={"product_name": "品項", "spec": "規格", "quantity": "數量", "unit_price": "單價", "amount": "金額"})
    
    df.to_excel(workbook, sheet_name='採購單', startrow=10, index=False)
    
    # 取得 workbook 和 worksheet 物件來做進階排版
    wb = workbook.book
    ws = workbook.sheets['採購單']
    
    # 定義格式
    fmt_title = wb.add_format({'bold': True, 'font_size': 18, 'align': 'center'})
    fmt_header = wb.add_format({'bold': True, 'font_size': 12})
    fmt_currency = wb.add_format({'num_format': '$#,##0'})
    
    # 寫入表頭資訊
    ws.merge_range('A1:E1', '採購訂單 (Purchase Order)', fmt_title)
    
    ws.write('A3', f"採購單號: {po_data['po_number']}", fmt_header)
    ws.write('D3', f"日期: {po_data['order_date']}", fmt_header)
    
    ws.write('A5', f"供應商: {po_data['partners']['name']}", fmt_header)
    ws.write('A6', f"地址: {supp_data.get('company_address', '')}")
    ws.write('A7', f"聯絡人: {supp_data.get('contact_person', '')}")
    
    ws.write('A9', "專案代號: " + po_data['project_code'])
    
    # 調整欄寬
    ws.set_column('A:A', 20) # 品項
    ws.set_column('B:B', 15) # 規格
    ws.set_column('C:C', 10) # 數量
    ws.set_column('D:D', 15) # 單價
    ws.set_column('E:E', 15) # 金額
    
    # 寫入總計與簽核欄
    last_row = 10 + len(df) + 2
    ws.write(last_row, 3, "總計 (含稅):", fmt_header)
    ws.write(last_row, 4, po_data['total_amount'], fmt_currency)
    
    ws.write(last_row + 3, 0, "核准 (Approved By):", fmt_header)
    ws.write(last_row +
