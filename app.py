import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Chuski Live Candy", layout="wide")
st.title("🍧 Chuski Live Candy Management System")

INV_DB = "invoice_history.csv"
STOCK_DB = "stock_inventory.csv"

# Load menu directly from the Excel file
@st.cache_data
def load_menu():
    excel_file = "DOC-20260615-WA0016 (1) OR - Copy.xlsx"
    if os.path.exists(excel_file):
        try:
            df = pd.read_excel(excel_file, sheet_name='📥 ઓર્ડર એન્ટ્રી', skiprows=9)
            df = df.dropna(subset=['Flavor Name', 'Price'])
            return df.set_index('Flavor Name')['Price'].to_dict()
        except Exception:
            pass
    return {"Orange Ice Candy": 5, "Sp. Mava Rabdi Ice Candy": 30, "Rose Gulkand Ice Candy": 20}

MENU = load_menu()

# Initialize files if they don't exist
if not os.path.exists(INV_DB):
    pd.DataFrame(columns=["Invoice_ID", "Date", "Candy_Name", "Qty", "Rate", "Total_Amount"]).to_csv(INV_DB, index=False)
if not os.path.exists(STOCK_DB):
    initial_stock = pd.DataFrame([{"Candy_Name": name, "Available_Stock": 500} for name in MENU.keys()])
    initial_stock.to_csv(STOCK_DB, index=False)

choice = st.sidebar.radio("Go To", ["📝 Create Invoice", "📊 Reports", "📦 Stock"])

if choice == "📝 Create Invoice":
    st.header("New Invoice")
    inv_df = pd.read_csv(INV_DB)
    next_id = 1 if inv_df.empty else inv_df["Invoice_ID"].max() + 1
    
    st.subheader(f"Invoice #INV-{next_id:04d}")
    date_sel = st.date_input("Date", datetime.now().date())
    
    col1, col2 = st.columns(2)
    cart = []
    stock_df = pd.read_csv(STOCK_DB)
    
    with col1:
        for idx, (candy, price) in enumerate(MENU.items()):
            match = stock_df[stock_df["Candy_Name"] == candy]
            curr_stock = match["Available_Stock"].values[0] if not match.empty else 100
            qty = st.number_input(f"{candy} (₹{price}) | Stock: {curr_stock}", min_value=0, step=1, key=f"q_{idx}")
            if qty > 0:
                cart.append({"Candy_Name": candy, "Qty": qty, "Rate": price, "Total_Amount": qty * price})
                
    with col2:
        if cart:
            cart_df = pd.DataFrame(cart)
            st.table(cart_df)
            st.metric("Total Amount", f"₹{cart_df['Total_Amount'].sum()}")
            if st.button("Save Invoice", type="primary"):
                for item in cart:
                    stock_df.loc[stock_df["Candy_Name"] == item["Candy_Name"], "Available_Stock"] -= item["Qty"]
                    new_row = pd.DataFrame([{"Invoice_ID": next_id, "Date": str(date_sel), "Candy_Name": item["Candy_Name"], "Qty": item["Qty"], "Rate": item["Rate"], "Total_Amount": item["Total_Amount"]}])
                    inv_df = pd.concat([inv_df, new_row], ignore_index=True)
                stock_df.to_csv(STOCK_DB, index=False)
                inv_df.to_csv(INV_DB, index=False)
                st.success("Invoice Saved!")
                st.rerun()

elif choice == "📊 Reports":
    st.header("Sales Reports")
    inv_df = pd.read_csv(INV_DB)
    if inv_df.empty:
        st.info("No sales yet.")
    else:
        st.metric("Total Revenue Collected", f"₹{inv_df['Total_Amount'].sum():,}")
        st.subheader("Sales Breakdown by Candy")
        summary = inv_df.groupby("Candy_Name")["Total_Amount"].sum()
        st.bar_chart(summary)
        st.dataframe(summary)

elif choice == "📦 Stock":
    st.header("Inventory Stock")
    stock_df = pd.read_csv(STOCK_DB)
    st.dataframe(stock_df.set_index("Candy_Name"))
