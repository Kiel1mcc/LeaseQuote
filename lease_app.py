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
from lease_calculations import calculate_base_and_monthly_payment

st.set_page_config(page_title="Lease Quote Calculator", layout="wide")

st.markdown("""
<style>
    .main {
        background-color: #ffffff;
        color: #1a1a1a;
        padding: 3rem 4rem;
        min-height: 100vh;
        font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .sidebar .stTextInput, .sidebar .stSelectbox, .sidebar .stNumberInput {
        margin-bottom: 2rem;
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #e0e7ff;
        transition: border-color 0.3s;
    }
    .sidebar .stTextInput input, .sidebar .stSelectbox select, .sidebar .stNumberInput input {
        color: #1a1a1a;
        background: transparent;
        border: none;
        font-size: 1.1rem;
    }
    .sidebar .stTextInput input:focus, .sidebar .stSelectbox select:focus, .sidebar .stNumberInput input:focus {
        outline: none;
        border-color: #60a5fa;
    }
    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #3b82f6);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem 2.5rem;
        font-weight: 600;
        font-size: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3);
    }
    .vehicle-info {
        background-color: #ffffff;
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
        border: 1px solid #e0e7ff;
        margin-bottom: 3rem;
        transition: transform 0.3s;
    }
    .vehicle-info:hover {
        transform: translateY(-4px);
    }
    .vehicle-row {
        display: grid;
        grid-template-columns: repeat(7, minmax(150px, 1fr));
        gap: 3.5rem;
        font-size: 1.1rem;
        color: #1a1a1a;
        font-weight: 500;
    }
    .vehicle-row div {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .lease-options-table {
        display: grid;
        grid-template-columns: 1fr repeat(3, minmax(180px, 1fr));
        gap: 1rem;
        margin-top: 2.5rem;
        align-items: center;
    }
    .lease-term, .mileage-header, .payment-value, .stExpander summary {
        font-size: 1.3rem;
        font-weight: 600;
        padding: 1rem;
        text-align: center;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s;
    }
    .lease-term {
        color: #64748b;
        background: #f1f5f9;
    }
    .mileage-header {
        color: #2563eb;
        background: #e0e7ff;
    }
    .payment-value {
        color: #1a1a1a;
        background: #ffffff;
    }
    .payment-value:hover {
        transform: translateY(-2px);
    }
    .lease-details {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
        margin-top: 1rem;
        border: 1px solid #e0e7ff;
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.5rem;
        align-items: center;
    }
    .detail-item {
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        background: #f8fafc;
    }
    .metric-label {
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .option-panel {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 12px;
        margin-top: 1.5rem;
        display: flex;
        gap: 1.5rem;
        flex-wrap: wrap;
        justify-content: flex-start;
        border: 1px solid #e0e7ff;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }
    .option-panel .stToggle, .option-panel .stNumberInput {
        margin: 0.75rem 0;
        color: #1a1a1a;
    }
    .option-panel .stNumberInput input {
        background: #ffffff;
        color: #1a1a1a;
        border-radius: 8px;
        border: 1px solid #e0e7ff;
    }
    .stExpander {
        border: 1px solid #e0e7ff;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    .stExpander summary {
        color: #2563eb;
        background: #e0e7ff;
        font-weight: 600;
        padding: 1rem;
        text-align: center;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s, background 0.3s;
    }
    .stExpander summary:hover {
        background: #c7d2fe;
        transform: translateY(-2px);
    }
    .sidebar .stHeader {
        color: #1e40af;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 2.5rem;
        text-transform: uppercase;
        letter-spacing: 0.1rem;
    }
    ::-webkit-scrollbar {
        width: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #f8fafc;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb {
        background: #60a5fa;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #3b82f6;
    }
    @media (max-width: 768px) {
        .vehicle-row {
            grid-template-columns: repeat(2, 1fr);
            gap: 2rem;
        }
        .lease-options-table {
            grid-template-columns: 1fr repeat(3, minmax(140px, 1fr));
        }
        .lease-details {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
county_rates = pd.read_csv("County_Tax_Rates.csv")

with st.sidebar:
    st.header("Lease Parameters")
    vin_input = st.text_input("Enter VIN:", value="", placeholder="Enter 17-digit VIN")
    selected_tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)], help="Select credit tier for lease terms")
    county_column = county_rates.columns[0]
    selected_county = st.selectbox("Select County:", county_rates[county_column], help="Select county for tax rate")
    money_down = st.number_input("Down Payment ($)", min_value=0.0, value=0.0, step=100.0, help="Enter down payment amount")

    st.subheader("Display Settings")
    show_money_factor = st.checkbox("Show Money Factor", value=True)
    show_residual = st.checkbox("Show Residual Value", value=True)
    show_monthly = st.checkbox("Show Monthly Payment", value=True)
