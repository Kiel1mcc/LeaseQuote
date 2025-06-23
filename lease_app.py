import streamlit as st
import pandas as pd
import numpy as np
from lease_calculations import calculate_base_and_monthly_payment, calculate_ccr_full

# Load data files
@st.cache_data
def load_inventory():
    df = pd.read_excel("Locator_Detail_Updated.xlsx")
    df.columns = df.columns.str.strip().str.lower()
    return df

@st.cache_data
def load_lease_programs():
    df = pd.read_csv("All_Lease_Programs_Database.csv")
    df.columns = df.columns.str.strip().str.lower()
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

vin_input = st.text_input("Enter VIN:").strip().upper()

if vin_input:
    vin_row = inventory_df[inventory_df['vin'] == vin_input]
    if vin_row.empty:
        st.error("VIN not found in inventory.")
    else:
        vehicle_info = vin_row.iloc[0]

        SP = vehicle_info['msrp']
        model_number = vehicle_info['modelnumber']
        trim = vehicle_info['trim'].lower()

        tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 6)])
        tier_column = tier.lower()
        county = st.selectbox("Select County:", ["Adams", "Allen", "Ashland", "Ashtabula", "Athens"])
        trade_value_input = st.number_input("Trade Value ($)", value=0.0)
        money_down_slider = st.number_input("Default Down Payment ($)", value=0.0)
        apply_markup = st.checkbox("Apply Money Factor Markup (+0.0004)")

        available_programs = lease_df[
            (lease_df['modelnumber'] == model_number) &
            (lease_df['trim'].str.lower() == trim)
        ]

        if available_programs.empty:
            st.error("No lease programs found for this VIN and trim.")
        else:
            for _, lease_data in available_programs.iterrows():
                term = lease_data['term']
                residual_value = lease_data['residual']
                money_factor = lease_data.get(tier_column, None)
                lease_cash = lease_data['leasecash']

                if pd.isna(money_factor):
                    continue

                tax_rate = 0.0725
                K = 0.0
                M = 900.0
                Q = 62.5
                F = money_factor + (0.0004 if apply_markup else 0.0)
                W = term
                τ = tax_rate
                RES = residual_value

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

                TV_hold = trade_value_input
                B_hold = money_down_slider

                TV_applied = min(deal_charges, TV_hold)
                remaining_charges = deal_charges - TV_applied

                B_applied = min(remaining_charges, B_hold)
                TV_final = TV_hold - TV_applied
                B_final = B_hold - B_applied
                adjusted_B = B_applied + TV_applied

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

                st.markdown(f"### 📄 {term}-Month Lease")
                st.markdown(f"**📊 Adjusted B (CCR Cash Applied): ${adjusted_B:,.2f}**")
                st.markdown(f"**💵 Monthly Payment: ${monthly_payment:,.2f}**")
                st.markdown(f"_Base: {debug_post.get('Base Payment', 0.0):.2f}, Tax: {debug_post.get('Tax Amount', 0.0):.2f}, CCR: {debug_post.get('CCR', 0.0):.2f}_")

                st.markdown("#### 🔍 Calculation Factors")
                st.code(f"""
Selling Price (SP): {SP}
Money Down (B): {B_final}
Trade-In (TV): {TV_final}
Lease Cash: 0.0
Doc + Acq Fee (M): {M}
Title + License (Q): {Q}
Residual (RES): {RES}
Money Factor (F): {F}
Term (W): {W}
Tax Rate (τ): {tax_rate}
                """)

                st.markdown(f"""
                - From Trade Value: ${TV_applied:,.2f}
                - From Cash Down: ${B_applied:,.2f}
                - Lease Cash: ${lease_cash:,.2f}
                """)
