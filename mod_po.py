import streamlit as st
import pandas as pd
import time
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
        
        # 供應商 (只抓 Supplier)
        res_supp = supabase.table("partners").select("id, name, credit_limit").eq("type", "Supplier").execute()
        supp_map = {s['name']: s for s in res_supp.data}
        supp_options = list(supp_map.keys())

        # 現有 PO (編輯用)
        res_po = supabase.table("purchase_orders").select("po_number").order("created_at", desc=True).execute()
        existing_pos = [p['po_number'] for p in res_po.data]
    except:
        st.error("資料讀取失敗，請檢查資料庫連線。")
        return

    # --- 2. 編輯/新增 切換 ---
    c_sel, _ = st.columns([3, 1])
    target_po = c_sel.selectbox("✏️ 選擇要編輯的採購單 (或建立新單)", ["(建立新採購單)"] + existing_pos)

    # Session State 初始化
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

    # --- 憲法 Dev Mode 一鍵填充 ---
    if st.session_state.get("dev_mode", False):
        with st.sidebar:
            st.markdown("### 🛠️ PO 開發工具")
            if st.button("🚀 填入測試採購 (Test PO)"):
                mock_items = pd.DataFrame([
                    {"品項": "PP塑膠粒-T500", "規格": "25kg/包", "數量": 200, "單價": 450},
                    {"品項": "色母-黑色", "規格": "1kg/罐", "數量": 10, "單價": 1000}
                ])
                mock_pays = pd.DataFrame([
                    {"期數": "月結60天", "預計付款日": date(2026, 3, 31), "金額": 100000}
                ])
                st.session_state.po_form_data = {
                    "po_no": "PO-20260115-001", 
                    "project_code": "", 
                    "supplier_name": supp_options[0] if supp_options else "",
                    "cost_item": "3.1 原料採購成本",
                    "order_date": date.today(), 
                    "tax_type": "含稅",
                    "items": mock_items, 
                    "payments": mock_pays
                }
                st.toast("✅ 測試數據已填入")
                time.sleep(0.5)
                st.rerun()

    form_data = st.session_state.po_form_data

    # --- 3. 採購表單 ---
    with st.container(border=True):
        st.subheader("📋 採購單詳細內容")
        with st.form("po_main_form"):
            # A. 表頭
            st.markdown("#### 1. 採購表頭 (Header)")
            c1, c2 = st.columns(2)
            
            # 專案選擇
            def_proj_idx = 0
            if form_data["project_code"]:
                for i, opt in enumerate(proj_options):
                    if opt.startswith(form_data["project_code"]):
                        def_proj_idx = i
                        break
            sel_proj = c1.selectbox("歸屬專案", [""] + proj_options, index=def_proj_idx + 1 if form_data["project_code"] else 0)
            
            # 供應商選擇
            def_supp_idx = 0
            if form_data["supplier_name"] in supp_options:
                def_supp_idx = supp_options.index(form_data["supplier_name"])
            sel_supp = c2.selectbox("供應商 (Supplier)", supp_options, index=def_supp_idx)

            # 顯示供應商額度
            supp_limit = 0
            if sel_supp:
                supp_limit = supp_map[sel_supp]['credit_limit']
                c2.caption(f"ℹ️ 該供應商交易額度上限: ${supp_limit:,.0f}")

            c3, c4, c5, c6 = st.columns(4)
            po_no = c3.text_input("採購單號", value=form_data["po_no"], disabled=(target_po != "(建立新採購單)"))
            
            # 科目選擇
            def_cost_idx = 0
            if form_data["cost_item"] in COST_ITEMS:
                def_cost_idx = COST_ITEMS.index(form_data["cost_item"])
            cost_item = c4.selectbox("歸屬費用科目", COST_ITEMS, index=def_cost_idx, help="這筆錢算在哪個成本頭上？")
            
            # 日期處理
            try:
                if isinstance(form_data["order_date"], str):
                    order_d = datetime.strptime(form_data["order_date"], "%Y-%m-%d").date()
                else:
                    order_d = form_data["order_date"]
            except: order_d = date.today()
            
            order_date = c5.date_input("採購日期", value=order_d)
            tax_type = c6.selectbox("稅別", ["含稅", "未稅"], index=0 if form_data["tax_type"] == "含稅" else 1)

            # B. 明細
            st.markdown("#### 2. 採購明細")
            edited_items = st.data_editor(
                form_data["items"], num_rows="dynamic", use_container_width=True, key=f"po_items_{target_po}",
                column_config={"數量": st.column_config.NumberColumn(min_value=1), "單價": st.column_config.NumberColumn(min_value=0)}
            )
            
            po_total = 0
            if not edited_items.empty:
                try:
                    edited_items["小計"] = edited_items["數量"].astype(float) * edited_items["單價"].astype(float)
                    po_total = edited_items["小計"].sum()
                except: pass
            st.metric("採購總額", f"${po_total:,.0f}")

            # C. 付款計畫
            st.markdown("#### 3. 付款計畫 (Payment Schedule)")
            
            # 日期防呆
            df_pay = form_data["payments"].copy()
            if not df_pay.empty and "預計付款日" in df_pay.columns:
                df_pay["預計付款日"] = pd.to_datetime(df_pay["預計付款日"]).dt.date
            
            edited_payments = st.data_editor(
                df_pay, num_rows="dynamic", use_container_width=True, key=f"po_pay_{target_po}",
                column_config={"預計付款日": st.column_config.DateColumn(format="YYYY-MM-DD", required=True), "金額": st.column_config.NumberColumn(required=True)}
            )
            
            pay_total = 0
            if not edited_payments.empty:
                try:
                    pay_total = edited_payments["金額"].sum()
                except: pass
                
            diff = po_total - pay_total
            
            # D. 檢核與風控 (憲法 5-2)
            is_valid = True
            
            # 1. 金額檢核
            if diff == 0 and po_total > 0:
                st.success(f"✅ 金額檢核通過：採購總額 ${po_total:,.0f} 與付款總額相符。")
            else:
                is_valid = False
                if po_total == 0:
                    st.warning("⚠️ 請輸入採購明細")
                else:
                    st.error(f"❌ 金額不符！差額: ${diff:,.0f}")

            # 2. Credit Limit 風控
            if sel_supp and supp_limit > 0 and po_total > supp_limit:
                is_valid = False
                st.error(f"⛔ 風控攔截：本單金額 ${po_total:,.0f} 已超過供應商額度上限 ${supp_limit:,.0f}！")

            # E. 存檔
            btn_txt = "💾 更新採購單" if target_po != "(建立新採購單)" else "💾 建立採購單"
            submitted = st.form_submit_button(btn_txt)
            
            if submitted:
                if not is_valid:
                    st.error("無法存檔，請修正上述錯誤 (金額不符或超過額度)。")
                elif not po_no or not sel_proj:
                    st.error("單號與專案為必填")
                else:
                    p_code = sel_proj.split(" | ")[0]
                    supp_id = supp_map[sel_supp]['id']
                    save_po(supabase, po_no, p_code, supp_id, cost_item, order_date, tax_type, po_total, edited_items, edited_payments)

    # --- 4. 列表 ---
    st.divider()
    if target_po == "(建立新採購單)":
        render_po_list(supabase)

# === Helpers ===
def get_empty_form():
    return {
        "po_no": "", "project_code": "", "supplier_name": "", "cost_item": "3.1 原料採購成本",
        "order_date": date.today(), "tax_type": "含稅",
        "items": pd.DataFrame([{"品項": "", "規格": "", "數量": 1, "單價": 0}]),
        "payments": pd.DataFrame([{"期數": "月結", "預計付款日": date.today(), "金額": 0}])
    }

def load_po_data(supabase, po_no):
    try:
        head = supabase.table("purchase_orders").select("*, partners(name)").eq("po_number", po_no).single().execute().data
        items = supabase.table("po_items").select("product_name, spec, quantity, unit_price").eq("po_number", po_no).execute().data
        pays = supabase.table("po_payments").select("term_name, expected_date, amount").eq("po_number", po_no).execute().data
        
        df_items = pd.DataFrame(items).rename(columns={"product_name": "品項", "spec": "規格", "quantity": "數量", "unit_price": "單價"})
        df_pays = pd.DataFrame(pays).rename(columns={"term_name": "期數", "expected_date": "預計付款日", "amount": "金額"})
        
        # 轉 Date 物件
        if not df_pays.empty and "預計付款日" in df_pays.columns:
            df_pays["預計付款日"] = pd.to_datetime(df_pays["預計付款日"]).dt.date

        st.session_state.po_form_data = {
            "po_no": head["po_number"], "project_code": head["project_code"], 
            "supplier_name": head["partners"]["name"], "cost_item": head["cost_item"],
            "order_date": datetime.strptime(head["order_date"], "%Y-%m-%d").date(),
            "tax_type": head["tax_type"], "items": df_items, "payments": df_pays
        }
    except Exception as e: 
        st.error(f"載入失敗: {e}")

def save_po(supabase, po_no, p_code, supp_id, cost_item, order_date, tax_type, total, items_df, pay_df):
    try:
        # Header
        supabase.table("purchase_orders").upsert({
            "po_number": po_no, "project_code": p_code, "supplier_id": supp_id, "cost_item": cost_item,
            "order_date": str(order_date), "tax_type": tax_type, "total_amount": total, "status": "Confirmed"
        }).execute()
        
        # Items
        supabase.table("po_items").delete().eq("po_number", po_no).execute()
        items_data = []
        for _, r in items_df.iterrows():
            if r.get("品項"):
                amt = float(r["數量"]) * float(r["單價"])
                items_data.append({"po_number": po_no, "product_name": r["品項"], "spec": r.get("規格"), "quantity": r["數量"], "unit_price": r["單價"], "amount": amt})
        if items_data: supabase.table("po_items").insert(items_data).execute()

        # Payments
        supabase.table("po_payments").delete().eq("po_number", po_no).execute()
        pay_data = []
        for _, r in pay_df.iterrows():
            if r["金額"] > 0:
                pay_data.append({"po_number": po_no, "term_name": r.get("期數"), "expected_date": str(r["預計付款日"]), "amount": float(r["金額"])})
        if pay_data: supabase.table("po_payments").insert(pay_data).execute()

        # Sync Matrix
        sync_po_matrix(supabase, p_code, cost_item)

        st.success("✅ 採購單儲存成功，費用已計入矩陣！")
        st.session_state.current_po_target = "(建立新採購單)"
        st.session_state.po_form_data = get_empty_form()
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"存檔失敗: {e}")

def sync_po_matrix(supabase, p_code, cost_item):
    # 算出該專案、該科目下，所有 PO 的付款計畫
    res = supabase.table("po_payments").select("expected_date, amount, purchase_orders!inner(project_code, cost_item)")\
        .eq("purchase_orders.project_code", p_code)\
        .eq("purchase_orders.cost_item", cost_item)\
        .execute()
    
    monthly_cost = {}
    if res.data:
        for row in res.data:
            d = datetime.strptime(row['expected_date'], "%Y-%m-%d")
            m_key = d.replace(day=1).strftime("%Y-%m-%d")
            monthly_cost[m_key] = monthly_cost.get(m_key, 0) + row['amount']
    
    # 寫入矩陣
    for m, amt in monthly_cost.items():
        # 讀取舊 Plan
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
        else:
            st.info("尚無採購單")
    except: pass
