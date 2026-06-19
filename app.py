import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Chuski Live Candy", layout="wide")
st.title("🍧 Chuski Live Candy Management System")

# Files to keep database records securely
INV_DB = "invoice_history.csv"
STOCK_DB = "stock_inventory.csv"
MENU_DB = "candy_menu.csv"

# --- INITIALIZE DATABASE FILES ---
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

# --- NAVIGATION MENU ---
choice = st.sidebar.radio("Go To", ["📝 Home & Create Invoice", "📊 Date-Wise & Monthly Reports", "⚙️ Price Settings", "📦 Stock Tracker"])

# ----------------------------------------------------
# 📝 TAB 1: HOME & CREATE INVOICE (SHOWS CREATED INVOICES)
# ----------------------------------------------------
if choice == "📝 Home & Create Invoice":
    st.header("🛒 Billing & Saved Invoices Dashboard")
    inv_df = pd.read_csv(INV_DB)
    next_id = 1 if inv_df.empty else int(inv_df["Invoice_ID"].max()) + 1
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader(f"🆕 Create Invoice #INV-{next_id:04d}")
        date_sel = st.date_input("Billing Date", datetime.now().date())
        
        cart = []
        st.markdown("#### Select Quantities")
        for idx, (candy, price) in enumerate(MENU.items()):
            match = stock_df[stock_df["Candy_Name"] == candy]
            curr_stock = match["Available_Stock"].values[0] if not match.empty else 0
            qty = st.number_input(f"{candy} (₹{price}) | Stock: {curr_stock}", min_value=0, step=1, key=f"q_{idx}")
            if qty > 0:
                cart.append({"Candy_Name": candy, "Qty": qty, "Rate": price, "Total_Amount": qty * price})
                
        if cart:
            cart_df = pd.DataFrame(cart)
            grand_total = cart_df['Total_Amount'].sum()
            st.metric("Grand Total Amount Due", f"₹{grand_total:,}")
            
            if st.button("💾 SAVE INVOICE", type="primary", use_container_width=True):
                for item in cart:
                    stock_df.loc[stock_df["Candy_Name"] == item["Candy_Name"], "Available_Stock"] -= item["Qty"]
                    new_row = pd.DataFrame([{"Invoice_ID": next_id, "Date": str(date_sel), "Candy_Name": item["Candy_Name"], "Qty": item["Qty"], "Rate": item["Rate"], "Total_Amount": item["Total_Amount"]}])
                    inv_df = pd.concat([inv_df, new_row], ignore_index=True)
                
                stock_df.to_csv(STOCK_DB, index=False)
                inv_df.to_csv(INV_DB, index=False)
                st.success(f"🎉 Invoice #INV-{next_id:04d} saved successfully!")
                st.rerun()

    with col2:
        st.subheader("📋 Saved Invoices History (Database)")
        if inv_df.empty:
            st.info("No saved invoices found yet. Create one on the left!")
        else:
            # Download button so you can download your invoice data to Excel/CSV anytime!
            csv_data = inv_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Download All Invoices as CSV file", data=csv_data, file_name="invoice_history_backup.csv", mime="text/csv")
            
            # Grouping to show distinct invoices cleanly
            display_df = inv_df.copy()
            display_df = display_df.sort_values(by="Invoice_ID", ascending=False)
            st.dataframe(display_df, use_container_width=True, height=600)

# ----------------------------------------------------
# 📊 TAB 2: DATE-WISE & MONTHLY REPORTS
# ----------------------------------------------------
elif choice == "📊 Date-Wise & Monthly Reports":
    st.header("📊 Detailed Sales Analysis")
    inv_df = pd.read_csv(INV_DB)
    
    if inv_df.empty:
        st.info("No sales transactions available to generate reports.")
    else:
        inv_df['Date'] = pd.to_datetime(inv_df['Date'])
        inv_df['Year_Month'] = inv_df['Date'].dt.strftime('%Y-%m')
        inv_df['Only_Date'] = inv_df['Date'].dt.strftime('%Y-%m-%d')
        
        tab_daily, tab_monthly = st.tabs(["📆 Specific Date Search", "📅 Monthly Summary"])
        
        with tab_daily:
            st.subheader("Check Candy Sales For a Particular Date")
            search_date = st.date_input("Select Date to View Sales", datetime.now().date())
            search_date_str = str(search_date)
            
            daily_filtered = inv_df[inv_df['Only_Date'] == search_date_str]
            
            if daily_filtered.empty:
                st.warning(f"No candies were sold on {search_date_str}.")
            else:
                st.metric("Total Revenue for Today", f"₹{daily_filtered['Total_Amount'].sum():,}")
                st.markdown("#### Candies Sold on This Date:")
                daily_summary = daily_filtered.groupby("Candy_Name").agg(
                    Quantities_Sold=("Qty", "sum"),
                    Revenue_Earned=("Total_Amount", "sum")
                )
                st.dataframe(daily_summary, use_container_width=True)
        
        with tab_monthly:
            st.subheader("Monthly Performance Breakdowns")
            selected_month = st.selectbox("Select Month", sorted(inv_df['Year_Month'].unique(), reverse=True))
            
            monthly_filtered = inv_df[inv_df['Year_Month'] == selected_month]
            
            m_col1, m_col2 = st.columns(2)
            m_col1.metric(f"Total Revenue for {selected_month}", f"₹{monthly_filtered['Total_Amount'].sum():,}")
            m_col2.metric("Total Invoices Issued", len(monthly_filtered['Invoice_ID'].unique()))
            
            st.markdown("#### Candy Item Breakdown For This Month:")
            monthly_summary = monthly_filtered.groupby("Candy_Name").agg(
                Total_Qty_Sold=("Qty", "sum"),
                Total_Revenue=("Total_Amount", "sum")
            ).sort_values(by="Total_Qty_Sold", ascending=False)
            
            st.dataframe(monthly_summary, use_container_width=True)
            st.bar_chart(monthly_summary["Total_Revenue"])

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
