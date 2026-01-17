import streamlit as st
import time

def show(supabase):
    st.markdown('<p class="main-header">⚙️ 系統參數設定 (System Settings)</p>', unsafe_allow_html=True)

    # --- 1. 讀取現有設定 ---
    try:
        # 只取第一筆，因為我們架構設計是單一公司實體
        res = supabase.table("company_settings").select("*").limit(1).execute()
        current_data = res.data[0] if res.data else {}
    except Exception as e:
        st.error(f"讀取設定失敗，請確認資料庫是否已建立 company_settings 表格。錯誤: {e}")
        return

    # --- 2. 設定表單 ---
    with st.container(border=True):
        st.subheader("🏢 我司基本資料 (My Company Profile)")
        st.caption("此處設定將自動帶入所有正式單據 (PO, Invoice, Delivery Note) 的表頭與頁尾。")

        with st.form("admin_settings_form"):
            c1, c2 = st.columns(2)
            name_zh = c1.text_input("公司全名 (中文)", value=current_data.get("company_name_zh", ""))
            name_en = c2.text_input("公司全名 (英文)", value=current_data.get("company_name_en", ""))
            
            c3, c4 = st.columns(2)
            tax_id = c3.text_input("統一編號 (Tax ID)", value=current_data.get("tax_id", ""))
            phone = c4.text_input("公司代表電話", value=current_data.get("phone", ""))

            address = st.text_input("公司登記地址 (Address)", value=current_data.get("address", ""))
            
            bank_info = st.text_area("銀行匯款資料 (Bank Info)", 
                                     value=current_data.get("bank_info", ""),
                                     height=100,
                                     help="顯示於 Invoice 底部供客戶匯款使用")

            submitted = st.form_submit_button("💾 儲存設定")
            
            if submitted:
                try:
                    # 準備寫入的資料
                    payload = {
                        "company_name_zh": name_zh,
                        "company_name_en": name_en,
                        "tax_id": tax_id,
                        "phone": phone,
                        "address": address,
                        "bank_info": bank_info,
                        "updated_at": "now()"
                    }

                    if current_data.get("id"):
                        # 如果已有資料，執行 Update
                        supabase.table("company_settings").update(payload).eq("id", current_data["id"]).execute()
                    else:
                        # 如果是第一次設定，執行 Insert
                        supabase.table("company_settings").insert(payload).execute()

                    st.success("✅ 設定已更新！單據輸出將立即生效。")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"儲存失敗: {e}")

    # --- 3. 其他系統資訊 (保留未來擴充) ---
    with st.expander("🛠️ 進階設定 (Advanced)", expanded=False):
        st.info("此區塊保留給未來功能：如 SMTP 郵件伺服器設定、Logo 圖片上傳路徑、API 金鑰管理等。")
