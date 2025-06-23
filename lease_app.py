import streamlit as st
import pandas as pd
import numpy as np
from lease_calculations import calculate_base_and_monthly_payment, calculate_ccr_full

# Load data files
@st.cache_data
def load_inventory():
    df = pd.read_excel("Locator_Detail_Updated.xlsx")
    df.columns = df.columns.str.strip().str.lower()  # Normalize column names
    return df

@st.cache_data
def load_lease_programs():
    df = pd.read_csv("All_Lease_Programs_Database.csv")
    df.columns = df.columns.str.strip().str.lower()  # Normalize column names
    return df

inventory_df = load_inventory()
lease_df = load_lease_programs()

st.set_page_config(page_title="Lease Quote Calculator", layout="wide")

st.markdown("""
<style>
.toggle-green .stToggleSwitch [data-baseweb="switch"] {
  background-color: #28a745 !important;
}
.toggle-red .stToggleSwitch [data-baseweb="switch"] {
  background-color: #dc3545 !important;
}
</style>
""", unsafe_allow_html=True)

# Inputs
vin_input = st.text_input("Enter VIN:")
vin_input = vin_input.strip().upper()

if vin_input:
    vin_row = inventory_df[inventory_df['vin'] == vin_input]
    if vin_row.empty:
        st.error("VIN not found in inventory.")
    else:
        vehicle_info = vin_row.iloc[0]

        st.write("DEBUG COLUMN NAMES:", list(vehicle_info.index))  # <-- Debug print
        st.write("DEBUG LEASE DF COLUMNS:", list(lease_df.columns))  # <-- New debug line

        SP = vehicle_info['msrp']
        model_number = vehicle_info['modelnumber']
        year = vehicle_info['model']

        tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 6)])
        county = st.selectbox("Select County:", ["Adams", "Allen", "Ashland", "Ashtabula", "Athens"])
        trade_value_input = st.number_input("Trade Value ($)", value=0.0)
        money_down_slider = st.number_input("Default Down Payment ($)", value=0.0)
        apply_markup = st.checkbox("Apply Money Factor Markup (+0.0004)")

        # Lookup lease program
        term = 36
        mileage = 12000

        lease_row = lease_df[
            (lease_df['model_year'] == year) &
            (lease_df['model_number'] == model_number) &
            (lease_df['lease_term'] == term) &
            (lease_df['trim'].str.lower() == vehicle_info['trim'].lower()) &
            (lease_df['tier'] == tier)
        ]

        if lease_row.empty:
            st.error("No lease program found for this VIN, tier, and term.")
        else:
            lease_data = lease_row.iloc[0]
            residual_value = lease_data['residual_value']
            money_factor = lease_data['money_factor']
            lease_cash = lease_data['lease_cash']

            tax_rate = 0.0725

            K = 0.0
            M = 900.0
            Q = 62.5
            F = money_factor + (0.0004 if apply_markup else 0.0)
            W = term
            τ = tax_rate
            RES = residual_value

            # Step 1: Initial TopVal calculation with no funds applied
            _, _, debug_pre = calculate_ccr_full(
                SP=SP,
                B=0.0,
                rebates=0.0,
                TV=0.0,
                K=K,
                M=M,
                Q=Q,
                RES=RES,
                F=F,
                W=W,
                τ=τ,
                adjust_negative=False
            )
            initial_topval = debug_pre.get("Initial TopVal", 0.0)
            deal_charges = max(0.0, -initial_topval)
            st.markdown(f"**🛠️ Deal Charges (Uncovered TopVal): ${deal_charges:,.2f}**")

            # Step 2: Prioritize trade value to cover deal charges
            TV_hold = trade_value_input
            B_hold = money_down_slider

            TV_applied = min(deal_charges, TV_hold)
            remaining_charges = deal_charges - TV_applied

            B_applied = min(remaining_charges, B_hold)

            TV_final = TV_hold - TV_applied
            B_final = B_hold - B_applied

            adjusted_B = B_applied + TV_applied

            # Final CCR calculation with true funds
            final_ccr, monthly_payment, debug_post = calculate_base_and_monthly_payment(
                SP=SP,
                B=B_final,
                rebates=0.0,
                TV=TV_final,
                K=K,
                M=M,
                Q=Q,
                RES=RES,
                F=F,
                W=W,
                τ=τ
            )

            # Display Output
            st.markdown(f"**📊 Adjusted B (CCR Cash Applied): ${adjusted_B:,.2f}**")
            st.markdown(f"**💵 Monthly Payment: ${monthly_payment:,.2f}**")
            st.markdown(f"_Base: {debug_post.get('Base Payment', 0.0):.2f}, Tax: {debug_post.get('Tax Amount', 0.0):.2f}, CCR: {debug_post.get('CCR', 0.0):.2f}_")

            st.markdown(f"""
            ## 🔍 How Deal Charges Were Covered:
            - From Trade Value: ${TV_applied:,.2f}
            - From Cash Down: ${B_applied:,.2f}
            """)
