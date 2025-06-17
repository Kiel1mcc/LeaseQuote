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
    selected_tier = st.selectbox("Select Tier:", ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5", "Tier 6", "Tier 7", "Tier 8"])
    county_column = county_rates.columns[0]
    selected_county = st.selectbox("Select County:", county_rates[county_column])
    money_down = st.number_input("Money Down ($)", min_value=0.0, value=0.0, step=100.0)

    st.markdown("---")
    st.subheader("Display Settings")
    show_money_factor = st.checkbox("Money Factor", value=True)
    show_residual_value = st.checkbox("Residual Value", value=True)
    show_monthly_payment = st.checkbox("Monthly Payment (w/ tax)", value=True)
    show_down_payment = st.checkbox("Down Payment", value=True)
    show_ccr = st.checkbox("Cap Cost Reduction (CCR)", value=False)
    show_ta = st.checkbox("Total Advance (TA)", value=False)
    show_amd = st.checkbox("Average Monthly Depreciation (AMD)", value=False)
    show_alc = st.checkbox("Average Lease Charge (ALC)", value=False)
    show_base = st.checkbox("Base Payment", value=False)
    show_tax = st.checkbox("Total Sales Tax", value=False)
    show_lease_cash = st.checkbox("Lease Cash Applied", value=False)
    show_selling_price = st.checkbox("Selling Price (Editable)", value=True)

if vin_input:
    vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
    if vin_data.empty:
        st.error("VIN not found in inventory. Please check the VIN and try again.")
    else:
        vin = vin_data["VIN"].values[0]
        year = vin_data["ModelYear"].values[0] if "ModelYear" in vin_data.columns else "N/A"
        make = vin_data["Make"].values[0] if "Make" in vin_data.columns else "N/A"
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
            for _, row in matching_programs.iterrows():
                term_col = next((col for col in ["LeaseTerm", "Lease_Term", "Term"] if col in row), None)
                if not term_col:
                    continue

                term_months = row[term_col]
                mf_col = f"Tier {tier_num}"
                if mf_col not in row or pd.isna(row[mf_col]):
                    continue

                markup_enabled = st.toggle("Apply MF Markup (+0.00040)", value=True, key=f"markup_{term_months}")
                base_mf = float(row[mf_col])
                mf_to_use = base_mf + 0.00040 if markup_enabled else base_mf
                residual_percent = float(row["Residual"])
                residual_value = round(msrp * residual_percent, 2)
                default_lease_cash = float(row["LeaseCash"]) if "LeaseCash" in row else 0.0

                st.markdown(f"#### {term_months}-Month Lease")

                selling_price = st.number_input("Selling Price ($)", value=msrp, step=100.0, key=f"selling_price_{term_months}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    lease_cash_enabled = st.toggle("Apply Lease Cash", value=False, key=f"toggle_{term_months}")
                with col2:
                    lease_cash_input = st.number_input(
                        "Lease Cash ($)",
                        value=default_lease_cash,
                        min_value=0.0,
                        step=100.0,
                        disabled=not lease_cash_enabled,
                        key=f"lease_cash_{term_months}"
                    )

                applied_lease_cash = lease_cash_input if lease_cash_enabled else 0.0
                total_ccr = money_down + applied_lease_cash

                payment_calc = calculate_base_and_monthly_payment(
                    S=selling_price,
                    RES=residual_value,
                    W=term_months,
                    F=mf_to_use,
                    M=962.50,
                    Q=0,
                    B=total_ccr,
                    K=0,
                    U=0,
                    tau=tax_rate
                )

                st.markdown("<div class='lease-details'><div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;'>", unsafe_allow_html=True)

                if show_money_factor:
                    st.markdown(f"<div><p class='metric-label'>Money Factor</p><p class='metric-value'>{mf_to_use:.5f}</p></div>", unsafe_allow_html=True)
                    if markup_enabled:
                        st.markdown(f"<div><p class='metric-label' style='color:#999;'>Includes +0.00040 markup</p></div>", unsafe_allow_html=True)
                if show_residual_value:
                    st.markdown(f"<div><p class='metric-label'>Residual Value</p><p class='metric-value'>${residual_value:,.2f} ({residual_percent:.0%})</p></div>", unsafe_allow_html=True)
                if show_ccr:
                    st.markdown(f"<div><p class='metric-label'>Cap Cost Reduction (CCR)</p><p class='metric-value'>{payment_calc['Cap Cost Reduction']}</p></div>", unsafe_allow_html=True)
                if show_ta:
                    st.markdown(f"<div><p class='metric-label'>Total Advance (TA)</p><p class='metric-value'>{payment_calc['Total Advance']}</p></div>", unsafe_allow_html=True)
                if show_amd:
                    st.markdown(f"<div><p class='metric-label'>Average Monthly Depreciation (AMD)</p><p class='metric-value'>{payment_calc['Average Monthly Depreciation']}</p></div>", unsafe_allow_html=True)
                if show_alc:
                    st.markdown(f"<div><p class='metric-label'>Average Lease Charge (ALC)</p><p class='metric-value'>{payment_calc['Average Lease Charge']}</p></div>", unsafe_allow_html=True)
                if show_base:
                    st.markdown(f"<div><p class='metric-label'>Base Payment</p><p class='metric-value'>{payment_calc['Base Payment']}</p></div>", unsafe_allow_html=True)
                if show_monthly_payment:
                    st.markdown(f"<div><p class='metric-label'>Monthly Payment (w/ tax)</p><p class='metric-value'>{payment_calc['Monthly Payment']}</p></div>", unsafe_allow_html=True)
                if show_tax:
                    st.markdown(f"<div><p class='metric-label'>Total Sales Tax (over term)</p><p class='metric-value'>{payment_calc['Total Sales Tax']}</p></div>", unsafe_allow_html=True)
                if show_lease_cash:
                    st.markdown(f"<div><p class='metric-label'>Lease Cash Applied</p><p class='metric-value'>${applied_lease_cash:,.2f}</p></div>", unsafe_allow_html=True)
                if show_down_payment:
                    st.markdown(f"<div><p class='metric-label'>Down Payment</p><p class='metric-value'>${money_down:,.2f}</p></div>", unsafe_allow_html=True)
                if show_selling_price:
                    st.markdown(f"<div><p class='metric-label'>Selling Price</p><p class='metric-value'>${selling_price:,.2f}</p></div>", unsafe_allow_html=True)

                st.markdown("</div></div>", unsafe_allow_html=True)
