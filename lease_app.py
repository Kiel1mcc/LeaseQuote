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
    .lease-details {background-color: #ffffff; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 2rem;}
    .error {color: #d32f2f; font-weight: bold;}
    h1 {color: #003087; font-size: 2rem;}
    h3 {color: #003087; margin-top: 1.5rem;}
    .metric-label {font-size: 0.9rem; color: #555;}
    .metric-value {font-size: 1.1rem; font-weight: bold; color: #003087;}
</style>
""", unsafe_allow_html=True)

st.title("Lease Quote Calculator")

lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
county_rates = pd.read_csv("County_Tax_Rates.csv")

with st.sidebar:
    st.header("Lease Parameters")
    vin_input = st.text_input("Enter VIN:", value="")
    selected_tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
    county_column = county_rates.columns[0]
    selected_county = st.selectbox("Select County:", county_rates[county_column])
    money_down = st.number_input("Down Payment ($)", min_value=0.0, value=0.0, step=100.0)

if vin_input:
    vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
    if vin_data.empty:
        st.error("VIN not found in inventory. Please check the VIN and try again.")
    else:
        vin = vin_data["VIN"].values[0]
        year = vin_data.get("ModelYear", ["N/A"])[0]
        make = vin_data.get("Make", ["N/A"])[0]
        model = vin_data["Model"].values[0]
        trim = vin_data["Trim"].values[0]
        model_number = vin_data["ModelNumber"].values[0]
        msrp = vin_data["MSRP"].values[0]

        st.markdown("### Vehicle Information")
        st.markdown(f"""
        <div class="vehicle-info">
            <div class="vehicle-row">
                <div><b>VIN:</b> {vin}</div>
                <div><b>Year:</b> {year}</div>
                <div><b>Make:</b> {make}</div>
                <div><b>Model:</b> {model}</div>
                <div><b>Trim:</b> {trim}</div>
                <div><b>Model Number:</b> {model_number}</div>
                <div><b>MSRP:</b> ${msrp:,.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        lease_col = next((col for col in lease_programs.columns if col.strip().lower() == "modelnumber"), None)
        if not lease_col:
            st.error("ModelNumber column not found in lease program file.")
            st.stop()

        matching_programs = lease_programs[lease_programs[lease_col] == model_number]
        if matching_programs.empty:
            st.error("No lease programs found for this vehicle.")
        else:
            tier_num = int(selected_tier.split(" ")[1])
            rate_column = "Rate" if "Rate" in county_rates.columns else county_rates.columns[-1]
            tax_row = county_rates[county_rates[county_column] == selected_county]
            if tax_row.empty:
                st.error(f"Tax rate not found for selected county: {selected_county}")
                st.stop()
            tax_rate = tax_row[rate_column].values[0] / 100

            st.markdown("### Lease Options")
            term_col = next((col for col in matching_programs.columns if col.lower() in ["leaseterm", "lease_term", "term"]), None)
            if not term_col:
                st.error("Missing LeaseTerm column in the data.")
            else:
                terms = sorted(matching_programs[term_col].dropna().unique())
                mileage_options = [10000, 12000, 15000]
                for term in terms:
                    rows_for_term = matching_programs[matching_programs[term_col] == term]
                    for mileage in mileage_options:
                        row = rows_for_term.iloc[0]
                        mf_col = f"Tier {tier_num}"
                        if mf_col not in row or 'Residual' not in row or pd.isna(row[mf_col]) or pd.isna(row['Residual']):
                            continue

                        base_residual = float(row['Residual'])
                        if mileage == 10000 and term >= 33:
                            adjusted_residual = base_residual + 0.01
                        elif mileage == 15000:
                            adjusted_residual = base_residual - 0.02
                        else:
                            adjusted_residual = base_residual

                        selling_price = float(msrp)
                        apply_markup = True
                        mf = float(row[mf_col]) + (0.0004 if apply_markup else 0.0)
                        lease_cash = float(row["LeaseCash"]) if "LeaseCash" in row else 0.0
                        apply_cash = False
                        custom_cash = lease_cash
                        total_ccr = money_down + (custom_cash if apply_cash else 0.0)
                        residual_value = round(float(msrp) * adjusted_residual, 2)
                        payment_calc = calculate_base_and_monthly_payment(
                            S=selling_price,
                            RES=residual_value,
                            W=term,
                            F=mf,
                            M=962.50,
                            Q=0,
                            B=total_ccr,
                            K=0,
                            U=0,
                            tau=tax_rate
                        )

                        monthly_raw = payment_calc.get('Monthly Payment', '$0.00')
                        if isinstance(monthly_raw, str):
                            cleaned = monthly_raw.replace("$", "").replace(",", "")
                        else:
                            cleaned = monthly_raw
                        try:
                            initial_monthly_payment = float(cleaned)
                        except (ValueError, TypeError):
                            initial_monthly_payment = 0.0

                        try:
                            title = f"Monthly Payment: ${initial_monthly_payment:,.2f}"
                        except:
                            title = "Monthly Payment: —"

                        with st.expander(title, key=f"expander_{term}_{mileage}"):
                            st.number_input("Selling Price ($)", value=selling_price, step=100.0, key=f"selling_price_{term}_{mileage}", disabled=True)
                            st.number_input("Down Payment ($)", value=custom_cash, step=100.0, disabled=True, key=f"cash_input_{term}_{mileage}")

                            st.markdown(f"""
                            <div class="lease-details">
                                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                                    <div>
                                        <p class="metric-label">Mileage</p>
                                        <p class="metric-value">{mileage:,} mi/year</p>
                                    </div>
                                    <div>
                                        <p class="metric-label">Money Factor</p>
                                        <p class="metric-value">{mf:.5f}</p>
                                    </div>
                                    <div>
                                        <p class="metric-label">Residual Value</p>
                                        <p class="metric-value">${residual_value:,.2f} ({adjusted_residual:.0%})</p>
                                    </div>
                                    <div>
                                        <p class="metric-label">Monthly Payment</p>
                                        <p class="metric-value">{payment_calc['Monthly Payment']}</p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            st.toggle("Apply MF Markup (+0.00040)", value=apply_markup, key=f"mf_markup_{term}_{mileage}", disabled=True)
                            st.toggle("Apply Lease Cash", value=apply_cash, key=f"apply_cash_{term}_{mileage}", disabled=True)
