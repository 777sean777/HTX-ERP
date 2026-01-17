import streamlit as st
import pandas as pd
import time
import io
import os
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

        # 我司資料 (Company Info)
        res_comp = supabase.table("company_settings").select("*").limit(1).execute()
        my_company = res_comp.data[0] if res_comp.data else {}

        # 現有 PO
        res_po = supabase.table("purchase_orders").select("po_number").order("created_at", desc=True).execute()
        existing_pos = [p['po_number'] for p in res_po.data]
    except Exception as e:
        st.error(f"資料讀取失敗: {e}")
        return

    # --- 2. 編輯/新增 切換 ---
    c_sel, _ = st.columns([3, 1])
    target_po = c_sel.selectbox("✏️ 選擇要編輯的採購單 (或建立新單)", ["(建立新採購單)"] + existing_pos)

    if "current_po_target" not in st.session_state:
        st.session_state.current_po_target = "(建立新採購單)"
        st.session_state.po_form_data = get_empty_form(my_company)

    if st.session_state.current_po_target != target_po:
        st.session_state.current_po_target = target_po
        if target_po == "(建立新採購單)":
            st.session_state.po_form_data = get_empty_form(my_company)
            st.toast("已切換至新單模式")
        else:
            load_po_data(supabase, target_po)
            st.toast(f"已載入 {target_po}")

    # Dev Mode Fill
    if st.session_state.get("dev_mode", False):
        with st.sidebar:
            st.markdown("### 🛠️ PO 開發工具")
            if st.button("🚀 填入測試採購 (委外加工)"):
                mock_items = pd.DataFrame([
                    {"品項": "機能布料染色加工", "規格": "Navy Blue #202", "數量": 500, "單價": 45, "金額": 22500},
                    {"品項": "特殊潑水處理", "規格": "C0-DWR", "數量": 500, "單價": 15, "金額": 7500}
                ])
                mock_cpm = pd.DataFrame([
                    {"自備料品項": "胚布-T400", "規格": "60吋/Roll", "預計提供數量": 520, "單位": "碼", "備註": "含損耗4%"}
                ])
                mock_pays = pd.DataFrame([{"期數": "月結60天", "預計付款日": date(2026, 4, 30), "金額": 31500}])
                st.session_state.po_form_data.update({
                    "po_no": "PO-20260117-SUB01", 
                    "project_code": "", 
                    "supplier_name": supp_options[0] if supp_options else "",
                    "cost_item": "3.3 委外加工費用", 
                    "order_date": date.today(), 
                    "tax_type": "含稅",
                    "payment_terms": "月結 60 天",
                    "trade_terms": "當地交貨 (Delivered)",
                    "items": mock_items, 
                    "provided_materials": mock_cpm,
                    "payments": mock_pays
                })
                st.rerun()

    form_data = st.session_state.po_form_data

    # --- 3. 採購表單 (Input Area) ---
    with st.container(border=True):
        st.subheader("📋 採購單輸入 (Input)")
        with st.form("po_main_form"):
            # A. 表頭
            st.markdown("#### 1. 採購表頭 (Header)")
            c1, c2 = st.columns(2)
            
            # 專案
            def_proj_idx = 0
            if form_data["project_code"]:
                for i, opt in enumerate(proj_options):
                    if opt.startswith(form_data["project_code"]):
                        def_proj_idx = i
                        break
            sel_proj = c1.selectbox("歸屬專案", [""] + proj_options, index=def_proj_idx + 1 if form_data["project_code"] else 0)
            
            # 供應商
            def_supp_idx = 0
            if form_data["supplier_name"] in supp_options:
                def_supp_idx = supp_options.index(form_data["supplier_name"])
            sel_supp = c2.selectbox("供應商", supp_options, index=def_supp_idx)
            
            # 供應商額度提示
            supp_limit = 0
            if sel_supp:
                supp_limit = supp_map[sel_supp]['credit_limit']
                c2.caption(f"ℹ️ 額度上限: ${supp_limit:,.0f}")

            # 單號與日期
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
            
            tax_type = c6.selectbox("稅別", ["含稅", "未稅", "零稅"], index=["含稅", "未稅", "零稅"].index(form_data["tax_type"]))

            # 商務條件
            st.markdown("---")
            bc1, bc2 = st.columns(2)
            pay_terms = bc1.text_input("付款條件 (Payment Terms)", value=form_data.get("payment_terms", "月結 30 天"))
            trade_terms = bc2.selectbox("貿易條件 (Trade Terms)", ["當地交貨 (Delivered)", "Ex-Works (工廠交貨)", "FOB (船上交貨)", "CIF (含運保費)", "DDP (完稅交貨)"], index=0)

            # 物流資訊 (Ship To / Bill To)
            st.markdown("---")
            lc1, lc2 = st.columns(2)
            ship_to = lc1.text_area("送貨地址 (Ship To)", value=form_data.get("ship_to_address", my_company.get("address", "")), height=70)
            bill_to = lc2.text_area("發票地址 (Bill To)", value=form_data.get("bill_to_address", my_company.get("address", "")), height=70)
            contact = lc1.text_input("收貨聯絡人 (Contact)", value=form_data.get("receiver_contact", ""))

            # B. 採購明細
            st.markdown("#### 2. 採購明細 (Purchase Items)")
            st.caption("請輸入數量與單價，金額會自動計算。")
            
            editor_key = f"po_items_{target_po}"
            if editor_key in st.session_state:
                form_data["items"] = st.session_state[editor_key]

            if "金額" not in form_data["items"].columns:
                form_data["items"]["金額"] = 0

            if not form_data["items"].empty:
                form_data["items"]["數量"] = pd.to_numeric(form_data["items"]["數量"], errors='coerce').fillna(0)
                form_data["items"]["單價"] = pd.to_numeric(form_data["items"]["單價"], errors='coerce').fillna(0)
                form_data["items"]["金額"] = form_data["items"]["數量"] * form_data["items"]["單價"]

            edited_items = st.data_editor(
                form_data["items"], 
                num_rows="dynamic", 
                use_container_width=True, 
                key=editor_key,
                column_config={
                    "數量": st.column_config.NumberColumn(min_value=1, required=True), 
                    "單價": st.column_config.NumberColumn(min_value=0, required=True, format="$%d"),
                    "金額": st.column_config.NumberColumn(format="$%d", disabled=True) 
                }
            )
            
            raw_total = 0.0
            tax_amount = 0.0
            final_total = 0.0
            
            if not edited_items.empty:
                try:
                    sum_val = edited_items["金額"].sum()
                    if tax_type == "含稅":
                        final_total = sum_val
                        raw_total = sum_val / 1.05
                        tax_amount = final_total - raw_total
                    elif tax_type == "未稅":
                        raw_total = sum_val
                        tax_amount = raw_total * 0.05
                        final_total = raw_total + tax_amount
                    else: 
                        raw_total = sum_val
                        tax_amount = 0
                        final_total = raw_total
                except: pass

            k1, k2, k3 = st.columns(3)
            k1.metric("銷售額 (未稅)", f"${raw_total:,.0f}")
            k2.metric("營業稅 (5%)", f"${tax_amount:,.0f}")
            k3.metric("總計 (含稅)", f"${final_total:,.0f}")

            # C. 自備料明細
            st.markdown("#### 3. 自備料清單 (Provided Materials)")
            
            cpm_key = f"po_cpm_{target_po}"
            if cpm_key in st.session_state:
                form_data["provided_materials"] = st.session_state[cpm_key]

            edited_cpm = st.data_editor(
                form_data["provided_materials"],
                num_rows="dynamic",
                use_container_width=True,
                key=cpm_key,
                column_config={
                    "自備料品項": st.column_config.TextColumn(required=True),
                    "預計提供數量": st.column_config.NumberColumn(min_value=0),
                    "單位": st.column_config.TextColumn(width="small"),
                    "備註": st.column_config.TextColumn(width="large")
                }
            )

            # D. 付款計畫
            st.markdown("#### 4. 付款計畫 (Payment Schedule)")
            df_pay = form_data["payments"].copy()
            if not df_pay.empty and "預計付款日" in df_pay.columns:
                df_pay["預計付款日"] = pd.to_datetime(df_pay["預計付款日"]).dt.date
            
            edited_payments = st.data_editor(
                df_pay, num_rows="dynamic", use_container_width=True, key=f"po_pay_{target_po}",
                column_config={"預計付款日": st.column_config.DateColumn(format="YYYY-MM-DD", required=True), "金額": st.column_config.NumberColumn(required=True)}
            )
            
            pay_total = edited_payments["金額"].sum() if not edited_payments.empty else 0
            diff = final_total - pay_total
            
            # E. 檢核與存檔
            is_valid = True
            if abs(diff) < 1 and final_total > 0:
                st.success(f"✅ 金額相符")
            else:
                is_valid = False
                if final_total == 0: st.warning("⚠️ 請輸入明細")
                else: st.error(f"❌ 付款總額不符！差額: ${diff:,.0f}")

            if sel_supp and supp_limit > 0 and final_total > supp_limit:
                is_valid = False
                st.error(f"⛔ 超過額度上限 ${supp_limit:,.0f}！")

            btn_txt = "💾 更新採購單" if target_po != "(建立新採購單)" else "💾 建立採購單"
            submitted = st.form_submit_button(btn_txt)
            
            if submitted:
                if not is_valid: st.error("無法存檔，請修正錯誤。")
                elif not po_no or not sel_proj: st.error("必填欄位缺漏")
                else:
                    p_code = sel_proj.split(" | ")[0]
                    supp_id = supp_map[sel_supp]['id']
                    
                    save_data = {
                        "po_no": po_no, "p_code": p_code, "supp_id": supp_id, "cost_item": cost_item,
                        "order_date": order_date, "tax_type": tax_type, "total": final_total,
                        "payment_terms": pay_terms, "trade_terms": trade_terms,
                        "ship_to": ship_to, "bill_to": bill_to, "contact": contact
                    }
                    save_po(supabase, save_data, edited_items, edited_cpm, edited_payments)

    # --- 4. 輸出與列表 (Output Area) ---
    st.divider()
    
    if target_po != "(建立新採購單)":
        st.subheader("🖨️ 單據輸出中心")
        
        # 讀取完整資料 (含 Company Info)
        full_po_data = load_po_data_raw(supabase, target_po)
        
        if full_po_data:
            c_po, c_dn = st.columns(2)
            
            # 1. 下載正式 PO
            with c_po:
                excel_po = generate_excel_po(full_po_data, my_company)
                st.download_button(
                    label=f"📄 下載正式採購單 (PO)",
                    data=excel_po,
                    file_name=f"{target_po}_PO.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # 2. 下載自備料收貨單
            has_cpm = len(full_po_data.get('provided_materials', [])) > 0
            if has_cpm:
                with c_dn:
                    excel_dn = generate_excel_delivery_note(full_po_data, my_company)
                    st.download_button(
                        label=f"📦 下載自備料收貨單 (Delivery Note)",
                        data=excel_dn,
                        file_name=f"{target_po}_DeliveryNote.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                with c_dn:
                    st.info("此單無自備料，無需列印收貨單。")

    else:
        render_po_list(supabase)

# === Helpers ===
def get_empty_form(my_company):
    return {
        "po_no": "", "project_code": "", "supplier_name": "", "cost_item": "3.1 原料採購成本",
        "order_date": date.today(), "tax_type": "含稅",
        "payment_terms": "月結 60 天", "trade_terms": "當地交貨 (Delivered)",
        "ship_to_address": my_company.get("address", ""),
        "bill_to_address": my_company.get("address", ""),
        "receiver_contact": "",
        "items": pd.DataFrame([{"品項": "", "規格": "", "數量": 1, "單價": 0, "金額": 0}]),
        "provided_materials": pd.DataFrame([{"自備料品項": "", "規格": "", "預計提供數量": 0, "單位": "", "備註": ""}]),
        "payments": pd.DataFrame([{"期數": "月結", "預計付款日": date.today(), "金額": 0}])
    }

def load_po_data(supabase, po_no):
    try:
        head = supabase.table("purchase_orders").select("*, partners(name)").eq("po_number", po_no).single().execute().data
        items = supabase.table("po_items").select("product_name, spec, quantity, unit_price, amount").eq("po_number", po_no).execute().data
        cpm = supabase.table("po_provided_materials").select("material_name, spec, quantity, unit, remarks").eq("po_number", po_no).execute().data
        pays = supabase.table("po_payments").select("term_name, expected_date, amount").eq("po_number", po_no).execute().data
        
        df_items = pd.DataFrame(items).rename(columns={"product_name": "品項", "spec": "規格", "quantity": "數量", "unit_price": "單價", "amount": "金額"})
        df_cpm = pd.DataFrame(cpm).rename(columns={"material_name": "自備料品項", "spec": "規格", "quantity": "預計提供數量", "unit": "單位", "remarks": "備註"})
        if df_cpm.empty: df_cpm = pd.DataFrame([{"自備料品項": "", "規格": "", "預計提供數量": 0, "單位": "", "備註": ""}])

        df_pays = pd.DataFrame(pays).rename(columns={"term_name": "期數", "expected_date": "預計付款日", "amount": "金額"})
        if not df_pays.empty: df_pays["預計付款日"] = pd.to_datetime(df_pays["預計付款日"]).dt.date

        st.session_state.po_form_data = {
            "po_no": head["po_number"], "project_code": head["project_code"], 
            "supplier_name": head["partners"]["name"], "cost_item": head["cost_item"],
            "order_date": datetime.strptime(head["order_date"], "%Y-%m-%d").date(),
            "tax_type": head["tax_type"], 
            "payment_terms": head.get("payment_terms", ""), "trade_terms": head.get("trade_terms", ""),
            "ship_to_address": head.get("ship_to_address", ""), "bill_to_address": head.get("bill_to_address", ""),
            "receiver_contact": head.get("receiver_contact", ""),
            "items": df_items, "provided_materials": df_cpm, "payments": df_pays
        }
    except Exception as e: st.error(f"載入失敗: {e}")

def load_po_data_raw(supabase, po_no):
    try:
        head = supabase.table("purchase_orders").select("*, partners(*), project_code").eq("po_number", po_no).single().execute().data
        head['items'] = supabase.table("po_items").select("*").eq("po_number", po_no).execute().data
        head['provided_materials'] = supabase.table("po_provided_materials").select("*").eq("po_number", po_no).execute().data
        
        if head.get('partners'):
            head['supplier_name'] = head['partners']['name']
        else:
            head['supplier_name'] = "Unknown Vendor"
            
        return head
    except Exception as e: 
        st.error(f"匯出數據讀取失敗: {e}")
        return None

def save_po(supabase, data, items_df, cpm_df, pay_df):
    try:
        supabase.table("purchase_orders").upsert({
            "po_number": data["po_no"], "project_code": data["p_code"], "supplier_id": data["supp_id"], 
            "cost_item": data["cost_item"], "order_date": str(data["order_date"]), "tax_type": data["tax_type"], 
            "total_amount": data["total"], "status": "Confirmed",
            "payment_terms": data["payment_terms"], "trade_terms": data["trade_terms"],
            "ship_to_address": data["ship_to"], "bill_to_address": data["bill_to"], "receiver_contact": data["contact"]
        }).execute()
        
        supabase.table("po_items").delete().eq("po_number", data["po_no"]).execute()
        items_list = []
        for _, r in items_df.iterrows():
            if r.get("品項"):
                items_list.append({
                    "po_number": data["po_no"], "product_name": r["品項"], "spec": r.get("規格"), 
                    "quantity": float(r["數量"]), "unit_price": float(r["單價"]), "amount": float(r["數量"])*float(r["單價"])
                })
        if items_list: supabase.table("po_items").insert(items_list).execute()

        supabase.table("po_provided_materials").delete().eq("po_number", data["po_no"]).execute()
        cpm_list = []
        for _, r in cpm_df.iterrows():
            if r.get("自備料品項"):
                cpm_list.append({
                    "po_number": data["po_no"], "material_name": r["自備料品項"], "spec": r.get("規格"),
                    "quantity": float(r["預計提供數量"]), "unit": r.get("單位"), "remarks": r.get("備註")
                })
        if cpm_list: supabase.table("po_provided_materials").insert(cpm_list).execute()

        supabase.table("po_payments").delete().eq("po_number", data["po_no"]).execute()
        pay_list = []
        for _, r in pay_df.iterrows():
            if r["金額"] > 0:
                pay_list.append({"po_number": data["po_no"], "term_name": r.get("期數"), "expected_date": str(r["預計付款日"]), "amount": float(r["金額"])})
        if pay_list: supabase.table("po_payments").insert(pay_list).execute()

        sync_po_matrix(supabase, data["p_code"], data["cost_item"])
        st.success("✅ 儲存成功！")
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

# --- Excel Generators ---
def generate_excel_po(po_data, my_company):
    output = io.BytesIO()
    workbook = pd.ExcelWriter(output, engine='xlsxwriter')
    wb = workbook.book
    pd.DataFrame().to_excel(workbook, sheet_name='PO', index=False)
    ws = workbook.sheets['PO']
    
    f_title = wb.add_format({'bold': True, 'font_size': 20, 'align': 'center'})
    f_bold = wb.add_format({'bold': True, 'font_size': 10})
    f_box = wb.add_format({'border': 1, 'text_wrap': True, 'valign': 'top', 'font_size': 10})
    f_header = wb.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1, 'align': 'center'})
    f_num = wb.add_format({'border': 1, 'num_format': '#,##0'})
    
    comp_name = my_company.get('company_name_zh', 'HTX')
    comp_addr = my_company.get('address', '')
    comp_tel = my_company.get('phone', '')
    
    # Logo Embedding
    if os.path.exists("logo.png"):
        ws.insert_image('A1', 'logo.png', {'x_scale': 0.5, 'y_scale': 0.5})
        ws.merge_range('C1:F1', "採購訂單 (PURCHASE ORDER)", f_title)
    else:
        ws.merge_range('A1:F1', "採購訂單 (PURCHASE ORDER)", f_title)

    ws.merge_range('A2:F2', f"{comp_name}\n地址: {comp_addr}\n電話: {comp_tel}", wb.add_format({'align': 'center', 'text_wrap': True}))
    
    ws.write('D4', "PO Number:", f_bold)
    ws.write('E4', po_data['po_number'])
    ws.write('D5', "Date:", f_bold)
    ws.write('E5', po_data['order_date'])
    ws.write('D6', "Project:", f_bold)
    ws.write('E6', po_data['project_code'])
    
    supp = po_data.get('partners') or {}
    ws.merge_range('A4:C4', "Vendor (供應商):", f_header)
    ws.merge_range('A5:C8', f"{supp.get('name', po_data.get('supplier_name', ''))}\n{supp.get('company_address','')}\nAttn: {supp.get('contact_person','')}\nTel: {supp.get('company_phone','')}", f_box)
    
    ws.merge_range('A10:C10', "Ship To (送貨地址):", f_header)
    ws.merge_range('A11:C13', f"{po_data.get('ship_to_address','')}\nAttn: {po_data.get('receiver_contact','')}", f_box)
    
    ws.merge_range('D10:F10', "Terms (條款):", f_header)
    ws.merge_range('D11:F13', f"Payment: {po_data.get('payment_terms','')}\nTrade: {po_data.get('trade_terms','')}\nTax: {po_data.get('tax_type','')}", f_box)

    row = 15
    headers = ["Item", "Description (Spec)", "Qty", "Unit", "Unit Price", "Amount"]
    for col, h in enumerate(headers):
        ws.write(row, col, h, f_header)
    
    row += 1
    for item in po_data['items']:
        ws.write(row, 0, item['product_name'], f_box)
        ws.write(row, 1, item['spec'], f_box)
        ws.write(row, 2, item['quantity'], f_box)
        ws.write(row, 3, "pcs", f_box)
        ws.write(row, 4, item['unit_price'], f_num)
        ws.write(row, 5, item['amount'], f_num)
        row += 1
        
    ws.write(row, 4, "Total:", f_bold)
    ws.write(row, 5, po_data['total_amount'], f_num)
    
    cpm = po_data.get('provided_materials', [])
    if cpm:
        row += 2
        ws.merge_range(row, 0, row, 5, "附件：自備料清單 (Materials Provided by Buyer)", f_header)
        row += 1
        ws.write(row, 0, "Item Name", f_bold)
        ws.write(row, 1, "Spec", f_bold)
        ws.write(row, 2, "Qty", f_bold)
        ws.write(row, 3, "Unit", f_bold)
        ws.write(row, 4, "Remarks", f_bold)
        row += 1
        for m in cpm:
            ws.write(row, 0, m['material_name'], f_box)
            ws.write(row, 1, m['spec'], f_box)
            ws.write(row, 2, m['quantity'], f_box)
            ws.write(row, 3, m['unit'], f_box)
            ws.write(row, 4, m['remarks'], f_box)
            row += 1

    row += 4
    ws.merge_range(row, 0, row, 2, "Confirmed By (Supplier):", f_header)
    ws.merge_range(row, 3, row, 5, "Approved By (Buyer):", f_header)
    ws.merge_range(row+1, 0, row+3, 2, "", f_box)
    ws.merge_range(row+1, 3, row+3, 5, "", f_box)

    ws.set_column('A:A', 20)
    ws.set_column('B:B', 25)
    ws.set_column('C:E', 10)
    ws.set_column('F:F', 15)
    
    workbook.close()
    return output.getvalue()

def generate_excel_delivery_note(po_data, my_company):
    output = io.BytesIO()
    workbook = pd.ExcelWriter(output, engine='xlsxwriter')
    wb = workbook.book
    pd.DataFrame().to_excel(workbook, sheet_name='DN', index=False)
    ws = workbook.sheets['DN']
    
    f_title = wb.add_format({'bold': True, 'font_size': 20, 'align': 'center'})
    f_bold = wb.add_format({'bold': True, 'font_size': 12})
    f_box = wb.add_format({'border': 1, 'text_wrap': True})
    f_header = wb.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1})
    
    # Logo for DN
    if os.path.exists("logo.png"):
        ws.insert_image('A1', 'logo.png', {'x_scale': 0.5, 'y_scale': 0.5})
        ws.merge_range('C1:E1', "自備料交貨單 (MATERIAL DELIVERY NOTE)", f_title)
    else:
        ws.merge_range('A1:E1', "自備料交貨單 (MATERIAL DELIVERY NOTE)", f_title)

    ws.merge_range('A2:E2', f"Ref PO No.: {po_data['po_number']}", wb.add_format({'align': 'center', 'font_size': 14, 'bold': True}))
    
    ws.write('A4', "To (Receiver):", f_bold)
    supp = po_data.get('partners') or {}
    ws.merge_range('B4:E4', f"{supp.get('name', po_data.get('supplier_name', 'Unknown'))}", f_box)
    ws.write('A5', "From (Sender):", f_bold)
    ws.merge_range('B5:E5', my_company.get('company_name_zh', 'HTX'), f_box)
    
    row = 7
    headers = ["Item Name", "Spec", "Quantity", "Unit", "Remarks"]
    for col, h in enumerate(headers):
        ws.write(row, col, h, f_header)
    
    row += 1
    for m in po_data.get('provided_materials', []):
        ws.write(row, 0, m['material_name'], f_box)
        ws.write(row, 1, m['spec'], f_box)
        ws.write(row, 2, m['quantity'], f_box)
        ws.write(row, 3, m['unit'], f_box)
        ws.write(row, 4, m['remarks'], f_box)
        row += 1
        
    row += 3
    ws.merge_range(row, 0, row, 4, "聲明：收到上述物料無誤，本批物料僅供指定 PO 訂單加工使用，加工完成後餘料需退回。", wb.add_format({'italic': True}))
    
    row += 2
    ws.write(row, 0, "Received By (Sign):", f_bold)
    ws.merge_range(row, 1, row, 2, "", wb.add_format({'bottom': 1}))
    ws.write(row, 3, "Date:", f_bold)
    ws.write(row, 4, "", wb.add_format({'bottom': 1}))

    ws.set_column('A:A', 20)
    ws.set_column('B:B', 20)
    ws.set_column('C:E', 15)

    workbook.close()
    return output.getvalue()
