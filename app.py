import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Chuski Live Candy", layout="wide")
st.title("🍧 Chuski Live Candy Management System")

# --- DATA STORAGE FILES ---
INV_DB = "invoice_history.csv"
STOCK_DB = "stock_inventory.csv"
MENU_DB = "candy_menu.csv"

# --- SYSTEM INITIALIZATION ---
if not os.path.exists(MENU_DB):
    initial_menu = {
        "Orange Ice Candy": 5.0, "Kala Khatta Ice Candy": 5.0, "Kachi Keri Ice Candy": 5.0,
        "Jamfal Ice Candy": 5.0, "Blueberi Ice Candy": 5.0, "Choko Moko Ice Candy": 20.0,
        "Rajbhog Ice Candy": 20.0, "Sp. Mava Rabdi Ice Candy": 30.0, "Sp. Kunafa Ice Candy": 50.0,
        "American Ice Candy": 30.0, "Pan Ice Candy": 20.0, "Rose Gulkand Ice Candy": 20.0,
        "Chiku Ice Candy": 20.0, "Topra Ice Candy": 20.0, "Dudh Khajur Ice Candy": 20.0,
        "Jambu Ice Candy": 20.0, "Mava Pista Ice Candy": 30.0, "Pineapple Ice Candy": 20.0,
        "Real Mango Ice Candy": 20.0
    }
    pd.DataFrame(list(initial_menu.items()), columns=["Candy_Name", "Price"]).to_csv(MENU_DB, index=False)

if not os.path.exists(INV_DB):
    pd.DataFrame(columns=["Invoice_ID", "Date", "Candy_Name", "Qty", "Rate", "Total_Amount"]).to_csv(INV_DB, index=False)

menu_df = pd.read_csv(MENU_DB)
MENU = menu_df.set_index('Candy_Name')['Price'].to_dict()

if not os.path.exists(STOCK_DB):
    pd.DataFrame([{"Candy_Name": name, "Available_Stock": 500} for name in MENU.keys()]).to_csv(STOCK_DB, index=False)

stock_df = pd.read_csv(STOCK_DB)
inv_df = pd.read_csv(INV_DB)

if "form_reset_token" not in st.session_state:
    st.session_state["form_reset_token"] = 0

# --- NAVIGATION ---
choice = st.sidebar.radio("Go To", ["📝 Home Dashboard", "📊 Date & Monthly Reports", "⚙️ Price Settings", "📦 Stock Tracker"])

# ----------------------------------------------------
# 📝 HOME DASHBOARD (WITH PRINTABLE INVOICES)
# ----------------------------------------------------
if choice == "📝 Home Dashboard":
    st.header("🛒 Billing & Live Records Panel")
    
    next_id = 1 if inv_df.empty else int(inv_df["Invoice_ID"].max()) + 1
    col1, col2 = st.columns([4, 5])
    
    # LEFT PANEL: INVOICE GENERATOR
    with col1:
        st.subheader(f"🆕 Current Invoice: #INV-{next_id:04d}")
        date_sel = st.date_input("Billing Date", datetime.now().date(), key=f"date_{st.session_state['form_reset_token']}")
        
        cart = []
        st.markdown("#### Select Quantities")
        for idx, (candy, price) in enumerate(MENU.items()):
            match = stock_df[stock_df["Candy_Name"] == candy]
            curr_stock = match["Available_Stock"].values[0] if not match.empty else 0
            
            qty = st.number_input(
                f"{candy} (₹{price}) | Stock: {curr_stock}", 
                min_value=0, step=1, 
                key=f"q_{idx}_{st.session_state['form_reset_token']}"
            )
            if qty > 0:
                cart.append({"Candy_Name": candy, "Qty": qty, "Rate": price, "Total_Amount": qty * price})
                
        if cart:
            cart_df = pd.DataFrame(cart)
            grand_total = cart_df['Total_Amount'].sum()
            st.metric("Grand Total Amount Due", f"₹{grand_total:,}")
            
            if st.button("💾 SAVE INVOICE RECORDS", type="primary", use_container_width=True):
                for item in cart:
                    stock_df.loc[stock_df["Candy_Name"] == item["Candy_Name"], "Available_Stock"] -= item["Qty"]
                    new_row = pd.DataFrame([{"Invoice_ID": next_id, "Date": str(date_sel), "Candy_Name": item["Candy_Name"], "Qty": item["Qty"], "Rate": item["Rate"], "Total_Amount": item["Total_Amount"]}])
                    inv_df = pd.concat([inv_df, new_row], ignore_index=True)
                
                stock_df.to_csv(STOCK_DB, index=False)
                inv_df.to_csv(INV_DB, index=False)
                
                st.success(f"🎉 Invoice #INV-{next_id:04d} saved to database history!")
                st.session_state["form_reset_token"] += 1
                st.rerun()

    # RIGHT PANEL: RECENT INVOICES LIST & PRINT SLIPS
    with col2:
        st.subheader("📋 Active Live Invoices List")
        if inv_df.empty:
            st.info("No active billing entries found.")
        else:
            csv_data = inv_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Download Database Backup (CSV)", data=csv_data, file_name="invoice_history.csv", mime="text/csv")
            st.markdown("---")
            
            unique_saved_ids = sorted(inv_df["Invoice_ID"].unique(), reverse=True)
            
            for target_id in unique_saved_ids:
                single_inv = inv_df[inv_df["Invoice_ID"] == target_id]
                inv_date = single_inv["Date"].values[0]
                inv_total = single_inv["Total_Amount"].sum()
                
                with st.container(border=True):
                    header_col, action_col = st.columns([2.5, 2])
                    
                    with header_col:
                        st.markdown(f"**🧾 Invoice #INV-{target_id:04d}** | 📅 *{inv_date}*")
                        st.markdown(f"💸 **Total Bill: ₹{inv_total:,}**")
                    
                    with action_col:
                        # --- GENERATE BEAUTIFUL HTML FOR PRINTING ---
                        table_rows = ""
                        for _, r in single_inv.iterrows():
                            table_rows += f"<tr><td style='padding:8px;'>{r['Candy_Name']}</td><td style='padding:8px;text-align:center;'>{r['Qty']}</td><td style='padding:8px;text-align:right;'>₹{r['Rate']}</td><td style='padding:8px;text-align:right;'>₹{r['Total_Amount']}</td></tr>"
                        
                        html_receipt = f"""
                        <div id="print-area-{target_id}" style="padding:20px; font-family:Arial, sans-serif; max-width:400px; border:1px solid #eee; margin:auto;">
                            <h2 style="text-align:center; color:#e056fd; margin-bottom:2px;">🍧 CHUSKI LIVE CANDY</h2>
                            <p style="text-align:center; font-size:12px; margin-top:0;">Pure Joy in Every Frozen Bite!</p>
                            <hr/>
                            <p><b>Invoice No:</b> #INV-{target_id:04d}<br/><b>Date:</b> {inv_date}</p>
                            <table style="width:100%; border-collapse:collapse; font-size:14px;">
                                <tr style="background:#f9f9f9; border-bottom:2px solid #ddd;"><th style="text-align:left; padding:8px;">Item</th><th style="padding:8px;">Qty</th><th style="text-align:right; padding:8px;">Rate</th><th style="text-align:right; padding:8px;">Total</th></tr>
                                {table_rows}
                            </table>
                            <hr/>
                            <h3 style="text-align:right; margin-top:10px;">Grand Total: ₹{inv_total:,}</h3>
                            <p style="text-align:center; font-size:12px; margin-top:20px; color:#777;">Thank You! Visit Again! 🙏</p>
                        </div>
                        <script>
                            function printInvoice_{target_id}() {{
                                var printContents = document.getElementById('print-area-{target_id}').innerHTML;
                                var originalContents = document.body.innerHTML;
                                document.body.innerHTML = printContents;
                                window.print();
                                document.body.innerHTML = originalContents;
                                window.location.reload();
                            }}
                        </script>
                        """
                        
                        # Printable slip launch button 
                        st.components.v1.html(
                            f"""
                            {html_receipt}
                            <button onclick="printInvoice_{target_id}()" style="width:100%; background-color:#2ed573; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer; font-size:14px;">🖨️ Print & Save PDF</button>
                            """,
                            height=45
                        )
                        
                        # Security
