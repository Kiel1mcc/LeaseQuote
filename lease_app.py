import streamlit as st
import pandas as pd
import numpy as np
from lease_calculations import calculate_base_and_monthly_payment, calculate_ccr_full

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
tier = st.selectbox("Select Tier:", ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"])
county = st.selectbox("Select County:", ["Adams", "Allen", "Ashland", "Ashtabula", "Athens"])
trade_value_input = st.number_input("Trade Value ($)", value=0.0)
money_down_slider = st.number_input("Default Down Payment ($)", value=0.0)
apply_markup = st.checkbox("Apply Money Factor Markup (+0.0004)")

# Placeholder vehicle data
selling_price = 25040
residual_value = 15255
money_factor = 0.00131
term = 36
tax_rate = 0.0725

# Fees and other variables
K = 0.0
M = 900.0
Q = 62.5
F = money_factor
W = term
τ = tax_rate
SP = selling_price
RES = residual_value
U = 0.0

# Step 1: Initial TopVal calculation with no funds applied
initial_ccr, _, debug_pre = calculate_ccr_full(
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

# What’s left after covering deal charges
TV_final = 0.0  # Not used to reduce SP after deal coverage
B_final = B_hold - B_applied  # Only excess B goes toward CCR

adjusted_B = B_applied + TV_applied

# Final CCR calculation with true funds
final_ccr, monthly_payment, debug_post = calculate_base_and_monthly_payment(
    SP=SP,
    B=B_final,
    rebates=0.0,
    TV=0.0,
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

st.markdown("""
## 🔍 How Deal Charges Were Covered:
- From Trade Value: ${TV_applied:,.2f}
- From Cash Down: ${B_applied:,.2f}
""")
