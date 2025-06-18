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
        background: linear-gradient(135deg, #0a192f, #1e3a8a);
        color: #e2e8f0;
        padding: 3rem 4rem;
        min-height: 100vh;
        font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .sidebar .stTextInput, .sidebar .stSelectbox, .sidebar .stNumberInput {
        margin-bottom: 2rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(5px);
        transition: border-color 0.3s, background 0.3s;
    }
    .sidebar .stTextInput input, .sidebar .stSelectbox select, .sidebar .stNumberInput input {
        color: #e2e8f0;
        background: transparent;
        border: none;
        font-size: 1.1rem;
    }
    .sidebar .stTextInput input:focus, .sidebar .stSelectbox select:focus, .sidebar .stNumberInput input:focus {
        outline: none;
        border-color: #60a5fa;
    }
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6, #9333ea);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 1rem 2.5rem;
        font-weight: 600;
        font-size: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 0.1rem;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.6);
    }
    .vehicle-info {
        background: rgba(255, 255, 255, 0.05);
        padding: 2.5rem;
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        margin-bottom: 3rem;
        transition: transform 0.3s;
    }
    .vehicle-info:hover {
        transform: translateY(-5px);
    }
    .vehicle-row {
        display: grid;
        grid-template-columns: repeat(7, minmax(150px, 1fr));
        gap: 3.5rem;
        font-size: 1.1rem;
        color: #e2e8f0;
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
        gap: 1.5rem;
        margin-top: 2.5rem;
    }
    .lease-term, .mileage-header {
        font-size: 1.3rem;
        font-weight: 600;
        padding: 1.2rem;
        text-align: center;
        border-radius: 10px;
    }
    .lease-term {
        color: #e2e8f0;
        background: rgba(255, 255, 255, 0.1);
    }
    .mileage-header {
        color: #60a5fa;
        background: rgba(96, 165, 250, 0.2);
    }
    .payment-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #e2e8f0;
        text-align: center;
        padding: 1.2rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s, background 0.3s;
    }
    .payment-value:hover {
        transform: translateY(-3px);
        background: rgba(255, 255, 255, 0.2);
    }
    .payment-value.lowest {
        background: #dc2626;
        color: #ffffff;
        font-weight: 800;
    }
    .lease-details {
        background: rgba(255, 255, 255, 0.05);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        margin-top: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(8px);
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 2rem;
    }
    .detail-item {
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        transition: transform 0.3s;
    }
    .detail-item.mileage {
        background: rgba(34, 197, 94, 0.1);
    }
    .detail-item.money-factor {
        background: rgba(59, 130, 246, 0.1);
    }
    .detail-item.residual-value {
        background: rgba(234, 179, 8, 0.1);
    }
    .detail-item.monthly-payment {
        background: rgba(239, 68, 68, 0.1);
    }
    .detail-item:hover {
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 1.1rem;
        color: #a3bffa;
        font-weight: 600;
        margin-bottom: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .metric-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 0.75rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .option-panel {
        background: rgba(255, 255, 255, 0.05);
        padding: 2rem;
        border-radius: 15px;
        margin-top: 1.5rem;
        display: flex;
        gap: 2rem;
        flex-wrap: wrap;
        justify-content: flex-start;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
    }
    .option-panel .stToggle, .option-panel .stNumberInput {
        margin: 1rem 0;
        color: #e2e8f0;
    }
    .option-panel .stNumberInput input {
        background: rgba(255, 255, 255, 0.1);
        color: #e2e8f0;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stExpander {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.03);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: all 0.3s;
    }
    .stExpander summary {
        font-weight: 600;
        color: #60a5fa;
        padding: 1rem;
        cursor: pointer;
        border-radius: 12px;
    }
    .stExpander summary:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    .sidebar .stHeader {
        color: #60a5fa;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 2.5rem;
        text-transform: uppercase;
        letter-spacing: 0.1rem;
    }
    ::-webkit-scrollbar {
        width: 12px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: #60a5fa;
        border-radius: 6px;
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

                st.markdown("<div class='lease-options-table'>", unsafe_allow_html=True)
                cols = st.columns([1] + [1] * len(mileage_options))
                cols[0].markdown("<div class='lease-term'>Term</div>", unsafe_allow_html=True)
                for i, mileage in enumerate(mileage_options):
                    cols[i + 1].markdown(f"<div class='mileage-header'>{mileage//1000}K Miles</div>", unsafe_allow_html=True)

                for term in rows_for_term:
                    row_group = rows_for_term[term]
                    cols = st.columns([1] + [1] * len(mileage_options))
                    cols[0].markdown(f"<div class='lease-term'>{term} Mo</div>", unsafe_allow_html=True)

                    min_payment = float('inf')
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
                        if initial_monthly_payment < min_payment:
                            min_payment = initial_monthly_payment

                        title = f"${initial_monthly_payment:,.2f}"

                        with cols[i + 1]:
                            payment_class = 'payment-value' + (' lowest' if initial_monthly_payment == min_payment else '')
                            st.markdown(f"<div class='{payment_class}'>{title}</div>", unsafe_allow_html=True)
                            with st.expander("View Details"):
                                st.markdown(f"""
                                <div class="lease-details">
                                    <div class="detail-item mileage">
                                        <p class="metric-label">Mileage</p>
                                        <p class="metric-value">{mileage:,} mi/year</p>
                                    </div>
                                    <div class="detail-item money-factor">
                                        <p class="metric-label">Money Factor</p>
                                        <p class="metric-value">{mf:.5f}</p>
                                    </div>
                                    <div class="detail-item residual-value">
                                        <p class="metric-label">Residual Value</p>
                                        <p class="metric-value">${residual_value:,.2f} ({adjusted_residual:.0%})</p>
                                    </div>
                                    <div class="detail-item monthly-payment">
                                        <p class="metric-label">Monthly Payment</p>
                                        <p class="metric-value">{payment_calc['Monthly Payment']}</p>
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
                st.markdown("</div>", unsafe_allow_html=True)
