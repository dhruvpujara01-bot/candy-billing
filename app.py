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
# 1. Build initial menu from the image list if MENU_DB doesn't exist
if not os.path.exists(MENU_DB):
    initial_menu = {
        "Orange Ice Candy": 5.0,
        "Kala Khatta Ice Candy": 5.0,
        "Kachi Keri Ice Candy": 5.0,
        "Jamfal Ice Candy": 5.0,
        "Blueberi Ice Candy": 5.0,
        "Choko Moko Ice Candy": 20.0,
        "Rajbhog Ice Candy": 20.0,
        "Sp. Mava Rabdi Ice Candy": 30.0,
        "Sp. Kunafa Ice Candy": 50.0,
        "American Ice Candy": 30.0,
        "Pan Ice Candy": 20.0,
        "Rose Gulkand Ice Candy": 20.0,
        "Chiku Ice Candy": 20.0,
        "Topra Ice Candy": 20.0,
        "Dudh Khajur Ice Candy": 20.0,
        "Jambu Ice Candy": 20.0,
        "Mava Pista Ice Candy": 30.0,
        "Pineapple Ice Candy": 20.0,
        "Real Mango Ice Candy": 20.0
    }
    df_m = pd.DataFrame(list(initial_menu.items()), columns=["Candy_Name", "Price"])
    df_m.to_csv(MENU_DB, index=False)

# 2. Invoices Database
if not os.path.exists(INV_DB):
    pd.DataFrame(columns=["Invoice_ID", "Date", "Candy_Name", "Qty", "Rate", "Total_Amount"]).to_csv(INV_DB, index=False)

# 3. Stock Tracker Database
if not os.path.exists(STOCK_DB):
    menu_df = pd.read_csv(MENU_DB)
    initial_stock = pd.DataFrame([{"Candy_Name": name, "Available_Stock": 500} for name in menu_df["Candy_Name"]])
    initial_stock.to_csv(STOCK_DB, index=False)

# --- LOAD CURRENT ACTIVE DATA ---
menu_df = pd.read_csv(MENU_DB)
MENU = menu_df.set_index('Candy_Name')['Price'].to_dict()

# Sync stock list if any new candy was added later
stock_df = pd.read_csv(STOCK_DB)
missing_candies = [c for c in MENU.keys() if c not in stock_df["Candy_Name"].values]
if missing_candies:
    new_stocks = pd.DataFrame([{"Candy_Name": c, "Available_Stock": 500} for c in missing_candies])
    stock_df = pd.concat([stock_df, new_stocks], ignore_index=True)
    stock_df.to_csv(STOCK_DB, index=False)


# --- NAVIGATION MENU ---
choice = st.sidebar.radio("Go To", ["📝 Create & Save Invoice", "⚙️ Price & Item Settings", "📊 Sales Reports", "📦 Stock Tracker"])

# ----------------------------------------------------
# 📝 TAB 1: CREATE & SAVE INVOICE
# ----------------------------------------------------
if choice == "📝 Create & Save Invoice":
    st.header("🛒 Create New Bill")
    inv_df = pd.read_csv(INV_DB)
    next_id = 1 if inv_df.empty else int(inv_df["Invoice_ID"].max()) + 1
    
    st.subheader(f"Invoice ID: #INV-{next_id:04d}")
    date_sel = st.date_input("Billing Date", datetime.now().date())
    
    col1, col2 = st.columns(2)
    cart = []
    
    with col1:
        st.markdown("#### Select Quantities")
        for idx, (candy, price) in enumerate(MENU.items()):
            match = stock_df[stock_df["Candy_Name"] == candy]
            curr_stock = match["Available_Stock"].values[0] if not match.empty else 0
            
            # Form field layout
            qty = st.number_input(f"{candy} (₹{price}) | Stock: {curr_stock}", min_value=0, step=1, key=f"q_{idx}")
            if qty > 0:
                cart.append({"Candy_Name": candy, "Qty": qty, "Rate": price, "Total_Amount": qty * price})
                
    with col2:
        st.markdown("#### Invoice Preview")
        if cart:
            cart_df = pd.DataFrame(cart)
            st.dataframe(cart_df, use_container_width=True)
            
            grand_total = cart_df['Total_Amount'].sum()
            st.metric("Grand Total Amount Due", f"₹{grand_total:,}")
            
            # MAIN INVOICE SAVE BUTTON OPTION
            if st.button("💾 SAVE INVOICE", type="primary", use_container_width=True):
                for item in cart:
                    # Deduct the stock
                    stock_df.loc[stock_df["Candy_Name"] == item["Candy_Name"], "Available_Stock"] -= item["Qty"]
                    
                    # Store Invoice record
                    new_row = pd.DataFrame([{
                        "Invoice_ID": next_id,
                        "Date": str(date_sel),
                        "Candy_Name": item["Candy_Name"],
                        "Qty": item["Qty"],
                        "Rate": item["Rate"],
                        "Total_Amount": item["Total_Amount"]
                    }])
                    inv_df = pd.concat([inv_df, new_row], ignore_index=True)
                
                stock_df.to_csv(STOCK_DB, index=False)
                inv_df.to_csv(INV_DB, index=False)
                st.success(f"🎉 Invoice #INV-{next_id:04d} saved successfully!")
                st.balloons()
                st.utility.experimental_rerun() if hasattr(st, "utility") else st.rerun()
        else:
            st.info("Change item quantities on the left to start adding elements to the billing section.")

# ----------------------------------------------------
# ⚙️ TAB 2: PRICE & ITEM SETTINGS (CHANGE PRICES HERE)
# ----------------------------------------------------
elif choice == "⚙️ Price & Item Settings":
    st.header("⚙️ Menu Management Settings")
    
    col_edit, col_add = st.columns(2)
    
    with col_edit:
        st.subheader("✏️ Change Existing Candy Prices")
        selected_candy = st.selectbox("Select Candy to Modify", menu_df["Candy_Name"].tolist())
        current_price = menu_df.loc[menu_df["Candy_Name"] == selected_candy, "Price"].values[0]
        
        new_price = st.number_input(f"New Price for {selected_candy} (Current: ₹{current_price})", min_value=0.0, value=float(current_price), step=1.0)
        
        if st.button("Update Price Record", type="secondary"):
            menu_df.loc[menu_df["Candy_Name"] == selected_candy, "Price"] = new_price
            menu_df.to_csv(MENU_DB, index=False)
            st.success(f"Price for {selected_candy} updated to ₹{new_price}!")
            st.rerun()

    with col_add:
        st.subheader("➕ Add Brand New Candy Item")
        new_candy_name = st.text_input("Enter New Candy Flavor Name")
        new_candy_price = st.number_input("Set Initial Base Price (₹)", min_value=0.0, step=1.0, value=20.0)
        
        if st.button("Save & Register New Candy"):
            if new_candy_name.strip() == "":
                st.error("Flavor name cannot be blank!")
            elif new_candy_name in menu_df["Candy_Name"].values:
                st.error("This flavor name is already registered!")
            else:
                new_item_df = pd.DataFrame([{"Candy_Name": new_candy_name, "Price": new_candy_price}])
                menu_df = pd.concat([menu_df, new_item_df], ignore_index=True)
                menu_df.to_csv(MENU_DB, index=False)
                st.success(f"'{new_candy_name}' added to the store catalog at ₹{new_candy_price}!")
                st.rerun()

# ----------------------------------------------------
# 📊 TAB 3: SALES REPORTS
# ----------------------------------------------------
elif choice == "📊 Sales Reports":
    st.header("📊 Sales Aggregation Reports")
    inv_df = pd.read_csv(INV_DB)
    if inv_df.empty:
        st.info("No sales transactions have been generated yet.")
    else:
        st.metric("Cumulative Business Turnover", f"₹{inv_df['Total_Amount'].sum():,}")
        st.subheader("Gross Sales Revenue Contribution")
        summary = inv_df.groupby("Candy_Name")["Total_Amount"].sum()
        st.bar_chart(summary)
        st.dataframe(summary.to_frame(name="Total Earned (₹)"))

# ----------------------------------------------------
# 📦 TAB 4: STOCK TRACKER
# ----------------------------------------------------
elif choice == "📦 Stock Tracker":
    st.header("📦 Inventory Levels")
    st.dataframe(stock_df.set_index("Candy_Name"), use_container_width=True)
    
    st.markdown("---")
    st.subheader("Restock Units")
    restock_target = st.selectbox("Select Variant to Restock", stock_df["Candy_Name"].tolist())
    added_amt = st.number_input("Count of Incoming Inventory Units", min_value=1, step=1)
    if st.button("Confirm Restock Arrival"):
        stock_df.loc[stock_df["Candy_Name"] == restock_target, "Available_Stock"] += added_amt
        stock_df.to_csv(STOCK_DB, index=False)
        st.success(f"Added {added_amt} units to inventory for {restock_target}!")
        st.rerun()
