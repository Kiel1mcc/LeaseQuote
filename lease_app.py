# NOTE TO GROK OR ANY OTHER ENGINEER WORKING ON THIS FILE:
# ------------------------------------------------------------
# DO NOT modify `lease_calculations.py` to import anything from this file.
# This file (lease_app.py) is the Streamlit app entry point.
# It imports `calculate_base_and_monthly_payment` from lease_calculations.py.
# If you reverse that or add circular references, it will break the app.
# Keep all styling changes in this file. All math logic should live in lease_calculations.py only.

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from lease_calculations import calculate_base_and_monthly_payment

st.set_page_config(page_title="Lease Quote Calculator", layout="wide")

st.markdown("""
<style>
    .main {background-color: #f9f9f9;}
    .sidebar .stTextInput, .sidebar .stSelectbox, .sidebar .stNumberInput {margin-bottom: 1rem;}
    .stButton>button {background-color: #0066cc; color: white; border-radius: 5px;}
    .stButton>button:hover {background-color: #0055b3;}
    .vehicle-info {background-color: #e6f0fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;}
    .vehicle-row {display: grid; grid-template-columns: repeat(7, minmax(100px, 1fr)); gap: 1.5rem; font-size: 0.95rem;}
    .vehicle-row div {white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
    .lease-details {background-color: #ffffff; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.06); margin-top: 1rem;}
    .error {color: #d32f2f; font-weight: bold;}
    h1 {color: #003087; font-size: 2rem;}
    h3 {color: #003087; margin-top: 1.5rem;}
    .metric-label {font-size: 0.85rem; color: #777; margin-bottom: 0.25rem;}
    .metric-value {font-size: 1.2rem; font-weight: 600; color: #222; margin-bottom: 1rem;}
    .option-panel {background-color: #f0f4f8; padding: 1.25rem; border-radius: 6px; margin-top: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; justify-content: flex-start;}
    .option-panel .stToggle, .option-panel .stNumberInput {margin: 0.5rem 0;}
</style>
""", unsafe_allow_html=True)

# Initialize variables
term = 36
mileage = 12000
initial_monthly_payment = 0.0
mf = 0.0
residual_value = 0.0
adjusted_residual = 0.0
payment_calc = {"Monthly Payment": "$0.00"}
apply_markup = False
apply_cash = False
custom_cash = 0.0

try:
    title = f"Monthly Payment: ${initial_monthly_payment:,.2f}"
except:
    title = "Monthly Payment"

with st.expander(title, key=f"expander_{term}_{mileage}"):
    st.markdown(f"""
    <div class="lease-details">
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem;">
            <div>
                <p class="metric-label">📈 Mileage</p>
                <p class="metric-value">{mileage:,} mi/year</p>
            </div>
            <div>
                <p class="metric-label">💰 Money Factor</p>
                <p class="metric-value">{mf:.5f}</p>
            </div>
            <div>
                <p class="metric-label">📉 Residual Value</p>
                <p class="metric-value">${residual_value:,.2f} ({adjusted_residual:.0%})</p>
            </div>
            <div>
                <p class="metric-label">📆 Monthly Payment</p>
                <p class="metric-value">{payment_calc['Monthly Payment']}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.toggle("Apply MF Markup (+0.00040)", value=apply_markup, key=f"mf_markup_{term}_{mileage}")
        with col2:
            st.toggle("Apply Lease Cash", value=apply_cash, key=f"apply_cash_{term}_{mileage}")
        with col3:
            st.number_input("Down Payment ($)", value=custom_cash, step=100.0, key=f"cash_input_{term}_{mileage}")
