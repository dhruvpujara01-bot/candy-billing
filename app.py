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
    pd.DataFrame(columns=["Invoice_ID", "Date", "Customer_Name", "Candy_Name", "Qty", "Rate", "Total_Amount"]).to_csv(INV_DB, index=False)

menu_df = pd.read_csv(MENU_DB)
MENU = menu_df.set_index('Candy_Name')['Price'].to_dict()

if not os.path.exists(STOCK_DB):
    pd.DataFrame([{"Candy_Name": name, "Available_Stock": 500} for name in MENU.keys()]).to_csv(STOCK_DB, index=False)

stock_df = pd.read_csv(STOCK_DB)

try:
    inv_df = pd.read_csv(INV_DB)
    if "Customer_Name" not in inv_df.columns:
        inv_df["Customer_Name"] = "Walk-in Customer"
except Exception:
    inv_df = pd.DataFrame(columns=["Invoice_ID", "Date", "Customer_Name", "Candy_Name", "Qty", "Rate", "Total_Amount"])

if "form_reset_token" not in st.session_state:
    st.session_state["form_reset_token"] = 0

# --- NAVIGATION ---
choice = st.sidebar.radio("Go To", ["📝 Home Dashboard", "📊 Date & Monthly Reports", "⚙️ Price Settings", "📦 Stock Tracker"])

# ----------------------------------------------------
# 📝 HOME DASHBOARD (FIXED NUMBER LOGIC FOR PRINT)
# ----------------------------------------------------
if choice == "📝 Home Dashboard":
    st.header("🛒 Billing & Live Records Panel")
    
    if inv_df.empty or "Invoice_ID" not in inv_df.columns or inv_df["Invoice_ID"].isna().all():
        next_id = 1
    else:
        next_id = int(inv_df["Invoice_ID"].max()) + 1
    
    col1, col2 = st.columns([4, 5])
    
    # LEFT PANEL: INVOICE GENERATOR
    with col1:
        st.subheader(f"🆕 Current Invoice: #INV-{next_id:04d}")
        
        cust_name = st.text_input("👤 Enter Customer Name", value="Walk-in Customer", key=f"cust_{st.session_state['form_reset_token']}")
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
                    new_row = pd.DataFrame([{
                        "Invoice_ID": int(next_id), 
                        "Date": str(date_sel), 
                        "Customer_Name": cust_name if cust_name.strip() != "" else "Walk-in Customer",
                        "Candy_Name": item["Candy_Name"], 
                        "Qty": int(item["Qty"]), 
                        "Rate": float(item["Rate"]), 
                        "Total_Amount": float(item["Total_Amount"])
                    }])
                    inv_df = pd.concat([inv_df, new_row], ignore_index=True)
                
                stock_df.to_csv(STOCK_DB, index=False)
                inv_df.to_csv(INV_DB, index=False)
                
                st.success(f"🎉 Invoice #INV-{next_id:04d} saved successfully!")
                st.session_state["form_reset_token"] += 1
                st.rerun()

    # RIGHT PANEL: RECORD CARDS WITH REBUILT FORMAT STRING TEMPLATE
    with col2:
        st.subheader("📋 Active Live Invoices List")
        if inv_df.empty:
            st.info("No active billing entries found yet.")
        else:
            all_csv = inv_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Download Complete Database Backup (CSV)", data=all_csv, file_name="all_invoices.csv", mime="text/csv")
            st.markdown("---")
            
            unique_saved_ids = sorted(inv_df["Invoice_ID"].dropna().unique(), reverse=True)
            
            for target_id in unique_saved_ids:
                single_inv = inv_df[inv_df["Invoice_ID"] == target_id]
                if single_inv.empty:
                    continue
                inv_date = single_inv["Date"].values[0]
                inv_total = float(single_inv["Total_Amount"].sum())
                inv_qty_total = int(single_inv["Qty"].sum())
                
                saved_cust_name = single_inv["Customer_Name"].values[0] if "Customer_Name" in single_inv.columns else "Walk-in Customer"
                formatted_id_str = f"{int(target_id):04d}" # Hard string block lock
                
                with st.container(border=True):
                    st.markdown(f"### 🧾 Invoice #INV-{formatted_id_str}")
                    st.write(f"👤 **Customer Name:** {saved_cust_name}")
                    st.write(f"📅 **Date:** {inv_date} | 🔢 **Total Qty:** {inv_qty_total} Pcs")
                    st.markdown(f"💰 **Grand Total Bill: ₹{inv_total:,.2f}**")
                    
                    table_rows = ""
                    sr_no = 1
                    for _, r in single_inv.iterrows():
                        table_rows += f"""
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 12px; text-align: center;">{sr_no}</td>
                            <td style="padding: 12px;">{r['Candy_Name']}</td>
                            <td style="padding: 12px; text-align: center;">{int(r['Qty'])}</td>
                            <td style="padding: 12px; text-align: right;">₹{float(r['Rate']):,.2f}</td>
                            <td style="padding: 12px; text-align: right;">₹{float(r['Total_Amount']):,.2f}</td>
                        </tr>
                        """
                        sr_no += 1
                    
                    html_code = f"""
                    <html>
                    <head>
                        <title>Invoice_INV_{formatted_id_str}</title>
                        <style>
                            @page {{
                                size: A4;
                                margin: 20mm;
                            }}
                            body {{
                                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                                color: #333;
                                margin: 0;
                                padding: 0;
                            }}
                            .invoice-box {{
                                width: 100%;
                                max-width: 800px;
                                margin: auto;
                            }}
                            .header-table {{
                                width: 100%;
                                margin-bottom: 50px;
                                border-collapse: collapse;
                            }}
                            .title-heading {{
                                color: #e056fd;
                                font-size: 34px;
                                margin: 0;
                                font-weight: bold;
                                letter-spacing: 1px;
                            }}
                            .main-table {{
                                width: 100%;
                                border-collapse: collapse;
                                margin-top: 30px;
                            }}
                            .main-table th {{
                                background-color: #f8f9fa;
                                color: #333;
                                font-weight: bold;
                                padding: 14px 12px;
                                border-bottom: 2px solid #333;
                                border-top: 1px solid #ddd;
                            }}
                            .info-data-cell {{
                                text-align: right; 
                                font-size: 15px; 
                                line-height: 1.8;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="invoice-box">
                            <table class="header-table">
                                <tr>
                                    <td style="vertical-align: top;">
                                        <h1 class="title-heading">🍧 CHUSKI LIVE CANDY</h1>
                                        <div style="font-size: 14px; color: #666; font-style: italic; margin-top: 4px;">Pure Joy in Every Frozen Bite!</div>
                                    </td>
                                    <td class="info-data-cell" style="vertical-align: top;">
                                        <div style="font-size: 26px; font-weight: bold; color: #333; margin-bottom: 12px; letter-spacing: 1px;">TAX INVOICE</div>
                                        <b>Invoice No:</b> #INV-{formatted_id_str}<br/>
                                        <b>Date:</b> {inv_date}<br/>
                                        <b>Customer Name:</b> {saved_cust_name}
                                    </td>
                                </tr>
                            </table>
                            
                            <table class="main-table">
                                <thead>
                                    <tr>
                                        <th style="width: 10%; text-align: center;">Sr No.</th>
                                        <th style="text-align: left;">Item Description</th>
                                        <th style="width: 15%; text-align: center;">Qty</th>
                                        <th style="width: 20%; text-align: right;">Rate</th>
                                        <th style="width: 20%; text-align: right;">Total Amount</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {table_rows}
                                    <tr style="font-weight: bold; font-size: 16px;">
                                        <td colspan="2" style="padding: 20px 10px; text-align: right; border-top: 2px solid #333;">TOTAL SUMMARY:</td>
                                        <td style="padding: 20px 10px; text-align: center; border-top: 2px solid #333;">{inv_qty_total} Pcs</td>
                                        <td style="border-top: 2px solid #333;"></td>
                                        <td style="padding: 20px 10px; text-align: right; color: #e056fd; border-top: 2px solid #333;">₹{inv_total:,.2f}</td>
                                    </tr>
                                </tbody>
                            </table>
                            
                            <div style="margin-top: 100px; text-align: center; border-top: 1px dashed #ccc; padding-top: 20px;">
                                <p style="font-size: 14px; color: #555; margin: 0;">Thank you for your business! Visit us again. 🙏</p>
                            </div>
                        </div>
                        <script>
                            window.onload = function() {{ window.print(); }}
                        </script>
                    </body>
                    </html>
                    """
                    
                    act_col1, act_col2 = st.columns(2)
                    with act_col1:
                        st.download_button(
                            label="🖨️ Download / Print A4 PDF",
                            data=html_code,
                            file_name=f"Invoice_INV_{formatted_id_str}.html",
                            mime="text/html",
                            key=f"print_html_{int(target_id)}",
                            use_container_width=True
                        )
                    with act_col2:
                        single_csv = single_inv.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download as CSV Data", 
                            data=single_csv, 
                            file_name=f"Invoice_INV_{formatted_id_str}.csv", 
                            mime="text/csv",
                            key=f"dl_csv_{int(target_id)}",
                            use_container_width=True
                        )
                        
                    u_col1, u_col2 = st.columns(2)
                    with u_col1:
                        edit_mode = st.checkbox("✏️ Edit Fields", key=f"edit_mode_{int(target_id)}")
                    with u_col2:
                        confirm_check = st.checkbox("🔓 Unlock Del", key=f"unlock_{int(target_id)}")
                    
                    if confirm_check:
                        if st.button("🚨 CONFIRM DELETE", key=f"del_btn_{int(target_id)}", type="primary", use_container_width=True):
                            inv_df = inv_df[inv_df["Invoice_ID"] != target_id]
                            inv_df.to_csv(INV_DB, index=False)
                            st.warning(f"Deleted #INV-{formatted_id_str}")
                            st.rerun()
                    
                    if edit_mode:
                        st.markdown("---")
                        st.markdown("#### ⚙️ Edit Fields Panel")
                        new_cust_field = st.text_input("Modify Customer Name", value=saved_cust_name, key=f"edit_cust_{int(target_id)}")
                        parsed_date = datetime.strptime(inv_date, '%Y-%m-%d').date() if isinstance(inv_date, str) else datetime.now().date()
                        new_inv_date = st.date_input("Modify Invoice Date", value=parsed_date, key=f"edit_date_field_{int(target_id)}")
                        
                        updated_lines = []
                        for line_idx, line_row in single_inv.iterrows():
                            st.write(f"🔹 *{line_row['Candy_Name']}*")
                            c_qty, c_rate = st.columns(2)
                            with c_qty:
                                new_line_qty = st.number_input("Qty", min_value=0, value=int(line_row['Qty']), key=f"eqty_{line_idx}")
                            with c_rate:
                                new_line_rate = st.number_input("Rate (₹)", min_value=0.0, value=float(line_row['Rate']), key=f"erate_{line_idx}")
                            
                            if new_line_qty > 0:
                                updated_lines.append({
                                    "Invoice_ID": target_id, 
                                    "Date": str(new_inv_date), 
                                    "Customer_Name": new_cust_field,
                                    "Candy_Name": line_row['Candy_Name'],
                                    "Qty": new_line_qty, "Rate": new_line_rate, "Total_Amount": new_line_qty * new_line_rate
                                })
                        
                        if st.button("💾 Apply Invoice Changes", key=f"save_edit_{int(target_id)}", type="primary", use_container_width=True):
                            inv_df = inv_df[inv_df["Invoice_ID"] != target_id]
                            if updated_lines:
                                inv_df = pd.concat([inv_df, pd.DataFrame(updated_lines)], ignore_index=True)
                            inv_df.to_csv(INV_DB, index=False)
                            st.success("Invoice lines adjusted safely!")
                            st.rerun()
                    else:
                        with st.expander("🔍 View Purchased Candy Details Table Grid"):
                            st.dataframe(single_inv[["Candy_Name", "Qty", "Rate", "Total_Amount"]].set_index("Candy_Name"), use_container_width=True)

# ----------------------------------------------------
# 📊 TAB 2: REPORTS
# ----------------------------------------------------
elif choice == "📊 Date & Monthly Reports":
    st.header("📊 Sales Reports")
    if inv_df.empty:
        st.info("No transaction data available yet.")
    else:
        inv_df['Date'] = pd.to_datetime(inv_df['Date'])
        inv_df['Year_Month'] = inv_df['Date'].dt.strftime('%Y-%m')
        inv_df['Only_Date'] = inv_df['Date'].dt.strftime('%Y-%m-%d')
        
        tab_daily, tab_monthly = st.tabs(["📆 Specific Date Search", "📅 Monthly Summary"])
        
        with tab_daily:
            search_date = st.date_input("Select Date", datetime.now().date())
            daily_filtered = inv_df[inv_df['Only_Date'] == str(search_date)]
            if daily_filtered.empty:
                st.warning(f"No transactions recorded on {search_date}.")
            else:
                st.metric("Daily Revenue Collected", f"₹{daily_filtered['Total_Amount'].sum():,}")
                daily_summary = daily_filtered.groupby(["Candy_Name", "Rate"]).agg(Quantities_Sold=("Qty", "sum"), Revenue_Earned=("Total_Amount", "sum")).reset_index()
                st.dataframe(daily_summary.set_index("Candy_Name"), use_container_width=True)
        
        with tab_monthly:
            selected_month = st.selectbox("Select Month", sorted(inv_df['Year_Month'].unique(), reverse=True))
            monthly_filtered = inv_df[inv_df['Year_Month'] == selected_month]
            
            m_col1, m_col2 = st.columns(2)
            m_col1.metric(f"Total Revenue for {selected_month}", f"₹{monthly_filtered['Total_Amount'].sum():,}")
            m_col2.metric("Total Invoices Issued", len(monthly_filtered['Invoice_ID'].unique()))
            
            monthly_summary = monthly_filtered.groupby(["Candy_Name", "Rate"]).agg(Total_Qty_Sold=("Qty", "sum"), Total_Revenue=("Total_Amount", "sum")).sort_values(by="Total_Qty_Sold", ascending=False).reset_index()
            st.dataframe(monthly_summary.set_index("Candy_Name"), use_container_width=True)

# ----------------------------------------------------
# ⚙️ TAB 3: PRICE SETTINGS
# ----------------------------------------------------
elif choice == "⚙️ Price Settings":
    st.header("⚙️ Menu Management Settings")
    col_edit, col_add = st.columns(2)
    with col_edit:
        st.subheader("✏️ Change Existing Candy Prices")
        selected_candy = st.selectbox("Select Candy to Modify", menu_df["Candy_Name"].tolist())
        current_price = menu_df.loc[menu_df["Candy_Name"] == selected_candy, "Price"].values[0]
        new_price = st.number_input(f"New Price for {selected_candy}", min_value=0.0, value=float(current_price))
        if st.button("Update Price Record"):
            menu_df.loc[menu_df["Candy_Name"] == selected_candy, "Price"] = new_price
            menu_df.to_csv(MENU_DB, index=False)
            st.success("Price updated successfully!")
            st.rerun()
    with col_add:
        st.subheader("➕ Add New Candy Flavor")
        new_candy_name = st.text_input("Enter New Flavor Name")
        new_candy_price = st.number_input("Set Price (₹)", min_value=0.0, value=20.0)
        if st.button("Save New Candy"):
            if new_candy_name and new_candy_name not in menu_df["Candy_Name"].values:
                new_row = pd.DataFrame([{"Candy_Name": new_candy_name, "Price": new_candy_price}])
                pd.concat([menu_df, new_row], ignore_index=True).to_csv(MENU_DB, index=False)
                st.success("New item added to store!")
                st.rerun()

# ----------------------------------------------------
# 📦 TAB 4: STOCK TRACKER
# ----------------------------------------------------
elif choice == "📦 Stock Tracker":
    st.header("📦 Inventory Levels")
    st.dataframe(stock_df.set_index("Candy_Name"), use_container_width=True)
    st.subheader("Restock Units")
    restock_target = st.selectbox("Select Variant to Restock", stock_df["Candy_Name"].tolist())
    added_amt = st.number_input("Count of Incoming Inventory Units", min_value=1, step=1)
    if st.button("Confirm Restock Arrival"):
        stock_df.loc[stock_df["Candy_Name"] == restock_target, "Available_Stock"] += added_amt
        stock_df.to_csv(STOCK_DB, index=False)
        st.success("Stock updated!")
        st.rerun()
