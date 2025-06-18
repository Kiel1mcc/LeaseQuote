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
        background-color: #1a202c;
        color: #e2e8f0;
        padding: 2rem;
        min-height: 100vh;
    }
    .sidebar .stTextInput, .sidebar .stSelectbox, .sidebar .stNumberInput {
        margin-bottom: 1.5rem;
        background-color: #2d3748;
        border-radius: 8px;
        padding: 0.5rem;
        color: #e2e8f0;
    }
    .sidebar .stTextInput input, .sidebar .stSelectbox select, .sidebar .stNumberInput input {
        color: #e2e8f0;
        background-color: transparent;
        border: none;
    }
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.8rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
    }
    .vehicle-info {
        background-color: #2d3748;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
        margin-bottom: 2rem;
        border: 1px solid #4b5563;
    }
    .vehicle-row {
        display: grid;
        grid-template-columns: repeat(7, minmax(130px, 1fr));
        gap: 2.5rem;
        font-size: 1rem;
        color: #e2e8f0;
    }
    .vehicle-row div {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .lease-details {
        background-color: #2d3748;
        padding: 2.5rem;
        border-radius: 14px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        margin-top: 2rem;
        border: 1px solid #4b5563;
    }
    .error {
        color: #fef2f2;
        font-weight: 600;
        background-color: #7f1d1d;
        padding: 1.25rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    h1 {
        color: #60a5fa;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 2rem;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
    }
    h3 {
        color: #60a5fa;
        font-size: 1.75rem;
        font-weight: 700;
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
    }
    .metric-label {
        font-size: 0.95rem;
        color: #9ca3af;
        font-weight: 500;
        margin-bottom: 0.6rem;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #e2e8f0;
        margin-bottom: 1.5rem;
    }
    .option-panel {
        background-color: #374151;
        padding: 2rem;
        border-radius: 12px;
        margin-top: 2rem;
        display: flex;
        gap: 2rem;
        flex-wrap: wrap;
        justify-content: flex-start;
        border: 1px solid #4b5563;
    }
    .option-panel .stToggle, .option-panel .stNumberInput {
        margin: 0.8rem 0;
        color: #e2e8f0;
    }
    .option-panel .stNumberInput input {
        background-color: #2d3748;
        color: #e2e8f0;
        border-radius: 8px;
    }
    .mileage-header {
        text-align: center;
        font-size: 1.3rem;
        font-weight: 700;
        color: #60a5fa;
        margin-bottom: 1.5rem;
        text-transform: uppercase;
    }
    .stExpander {
        border: 1px solid #4b5563;
        border-radius: 10px;
        background-color: #2d3748;
        transition: all 0.3s;
    }
    .stExpander summary {
        font-weight: 600;
        color: #3b82f6;
        padding: 1rem;
        cursor: pointer;
    }
    .stExpander summary:hover {
        background-color: #374151;
    }
    .sidebar .stHeader {
        color: #60a5fa;
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 2rem;
        text-transform: uppercase;
    }
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #2d3748;
    }
    ::-webkit-scrollbar-thumb {
        background: #60a5fa;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

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
            mileage_options = [10000, 12000, 15000]
            term_col = next((col for col in matching_programs.columns if col.lower() in ["leaseterm", "lease_term", "term"]), None)
            if not term_col:
                st.error("Missing LeaseTerm column in the data.")
            else:
                rows_for_term = {term: matching_programs[matching_programs[term_col] == term] for term in sorted(matching_programs[term_col].dropna().unique())}

                header_cols = st.columns(len(mileage_options) + 1)
                header_cols[0].markdown("#### Term")
                for i, mileage in enumerate(mileage_options):
                    header_cols[i+1].markdown(f"<div class='mileage-header'>{mileage//1000}K Miles</div>", unsafe_allow_html=True)

                for term in rows_for_term:
                    row_group = rows_for_term[term]
                    cols = st.columns(len(mileage_options) + 1)
                    cols[0].markdown(f"**{term} Mo**")

                    for i, mileage in enumerate(mileage_options):
                        row = row_group.iloc[0]
                        mf_col = f"Tier {tier_num}"
                        if mf_col not in row or 'Residual' not in row or pd.isna(row[mf_col]) or pd.isna(row['Residual']):
                            continue

                        base_residual = float(row['Residual'])
                        adjusted_residual = base_residual + 0.01 if mileage == 10000 else base_residual - 0.02 if mileage == 15000 else base_residual

                        selling_price = float(msrp)
                        apply_markup = True
                        mf = float(row[mf_col]) + (0.0004 if apply_markup else 0.0)
                        lease_cash = float(row["LeaseCash"]) if "LeaseCash" in row else 0.0
                        apply_cash = False
                        total_ccr = money_down + (lease_cash if apply_cash else 0.0)
                        residual_value = round(msrp * adjusted_residual, 2)

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
                        cleaned = monthly_raw.replace("$", "").replace(",", "") if isinstance(monthly_raw, str) else monthly_raw
                        initial_monthly_payment = float(cleaned)

                        title = f"${initial_monthly_payment:,.2f}"

                        with cols[i+1]:
                            st.markdown(f"<div class='metric-value'>{title}</div>", unsafe_allow_html=True)
                            with st.expander("View Details"):
                                st.markdown(f"""
                                <div class="lease-details">
                                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 3rem;">
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

                                st.markdown("<div class=\"option-panel\">", unsafe_allow_html=True)
                                col1, col2 = st.columns([1, 1])
                                with col1:
                                    st.toggle("Apply MF Markup (+0.00040)", value=apply_markup, key=f"mf_markup_{term}_{mileage}", disabled=True)
                                with col2:
                                    st.toggle("Apply Lease Cash", value=apply_cash, key=f"apply_cash_{term}_{mileage}", disabled=True)
                                st.number_input("Down Payment ($)", value=money_down, step=100.0, key=f"cash_input_{term}_{mileage}", disabled=True)
                                st.markdown("</div>", unsafe_allow_html=True)
