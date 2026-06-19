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

# --- NAVIGATION ---
choice = st.sidebar.radio("Go To", ["📝 Home Dashboard", "📊 Date & Monthly Reports", "⚙️ Price Settings", "📦 Stock Tracker"])

# ----------------------------------------------------
# 📝 HOME DASHBOARD (CREATE, VIEW, EDIT & DELETE HERE)
# ----------------------------------------------------
if choice == "📝 Home Dashboard":
    st.header("🛒 Billing & Records Central Control")
    next_id = 1 if inv_df.empty else int(inv_df["Invoice_ID"].max()) + 1
    
    col1, col2 = st.columns([4, 5])
    
    # LEFT PANEL: NEW INVOICE GENERATOR
    with col1:
        st.subheader(f"🆕 New Invoice #INV-{next_id:04d}")
        date_sel = st.date_input("Billing Date", datetime.now().date(), key="new_inv_date")
        
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

    # RIGHT PANEL: LIVE DATABASE MANAGEMENT (VIEW, DOWNLOAD, EDIT, DELETE)
    with col2:
        st.subheader("📋 Saved Invoices Database History")
        if inv_df.empty:
            st.info("No saved invoices found yet.")
        else:
            # Quick Action Section for Edit / Delete
            st.markdown("### ⚡ Quick Actions (Edit or Delete an Invoice)")
            unique_inv_ids = sorted(inv_df["Invoice_ID"].unique(), reverse=True)
            action_id = st.selectbox("Select Invoice ID to Edit or Delete", unique_inv_ids, key="action_inv_select")
            
            act_col1, act_col2 = st.columns(2)
            
            # --- ACTION 1: DELETE OPTION ---
            with act_col1:
                if st.button(f"🗑️ DELETE INVOICE #INV-{action_id:04d}", type="secondary", use_container_width=True):
                    # Remove from Database
                    inv_df = inv_df[inv_df["Invoice_ID"] != action_id]
                    inv_df.to_csv(INV_DB, index=False)
                    st.warning(f"💥 Invoice #INV-{action_id:04d} deleted completely!")
                    st.rerun()
            
            # --- ACTION 2: EDIT SYSTEM INLINE ---
            with act_col2:
                show_edit_panel = st.checkbox("✏️ Show Edit Inputs Panel", value=False)
                
            if show_edit_panel:
                st.markdown(f"#### Editing Invoice #INV-{action_id:04d} Below:")
                inv_rows = inv_df
