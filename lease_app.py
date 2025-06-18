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
    .main {
        background-color: #f8fafc;
        padding: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .sidebar .stTextInput, .sidebar .stSelectbox, .sidebar .stNumberInput {
        margin-bottom: 1.5rem;
        border-radius: 6px;
    }
    .stButton>button {
        background-color: #1e3a8a;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: background-color 0.2s;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1e40af;
    }
    .vehicle-info {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
        border: 1px solid #e2e8f0;
    }
    .vehicle-row {
        display: grid;
        grid-template-columns: repeat(7, minmax(100px, 1fr));
        gap: 2rem;
        font-size: 0.95rem;
        color: #1f2937;
    }
    .vehicle-row div {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .lease-details {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
        border: 1px solid #e2e8f0;
    }
    .error {
        color: #b91c1c;
        font-weight: 600;
        background-color: #fef2f2;
        padding: 1rem;
        border-radius: 6px;
    }
    h1 {
        color: #1e3a8a;
        font-size: 2.25rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
    }
    h3 {
        color: #1e3a8a;
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #4b5563;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e3a8a;
    }
    .stNumberInput input, .stSelectbox select, .stTextInput input {
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 0.5rem;
    }
    .stToggle label {
        font-size: 0.9rem;
        color: #1f2937;
    }
    /* Custom toggle styling */
    .stToggle input[type="checkbox"] {
        appearance: none;
        width: 40px;
        height: 20px;
        background-color: #e2e8f0;
        border-radius: 10px;
        position: relative;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .stToggle input[type="checkbox"]:checked {
        background-color: #1e3a8a;
    }
    .stToggle input[type="checkbox"]::before {
        content: '';
        position: absolute;
        width: 16px;
        height: 16px;
        background-color: #ffffff;
        border-radius: 50%;
        top: 2px;
        left: 2px;
        transition: transform 0.2s;
    }
    .stToggle input[type="checkbox"]:checked::before {
        transform: translateX(20px);
    }
    /* Styling for expander header */
    .st-expander {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .st-expander div[role="button"] {
        background-color: #ffffff;
        padding: 0.75rem 1rem;
        font-weight: 600;
        color: #1e3a8a;
    }
    .st-expander div[role="region"] {
        padding: 1rem;
        background-color: #f9fafb;
    }
</style>
""", unsafe_allow_html=True)

st.title("Lease Quote Calculator")

# Track whether the user has submitted a VIN so results persist
if "submitted" not in st.session_state:
    st.session_state.submitted = False

lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
county_rates = pd.read_csv("County_Tax_Rates.csv")

# Initialize session state with defaults
if 'default_apply_cash' not in st.session_state:
    st.session_state.default_apply_cash = False
if 'default_apply_markup' not in st.session_state:
    st.session_state.default_apply_markup = True
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

with st.sidebar:
    st.header("Lease Parameters")
    vin_input = st.text_input("Enter VIN:", value="", key="vin_input")
    selected_tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
    county_column = county_rates.columns[0]
    selected_county = st.selectbox("Select County:", county_rates[county_column])
    money_down = st.number_input("Money Down ($)", min_value=0.0, value=0.0, step=100.0)
    st.markdown("### Submit")
    submit_button = st.button("Submit")
    if submit_button:
        if st.session_state.vin_input:
            st.session_state.sidebar_open = False
            st.session_state.submitted = True
    st.markdown("### Display Settings")
    default_apply_cash = st.toggle(
        "Auto-apply Lease Cash",
        value=st.session_state.default_apply_cash,
        key="toggle_default_apply_cash",
    )
    if default_apply_cash != st.session_state.default_apply_cash:
        st.session_state.default_apply_cash = default_apply_cash
        for key in list(st.session_state.keys()):
            if key.startswith("applycash_"):
                st.session_state[key] = default_apply_cash

    default_apply_markup = st.toggle(
        "Auto-apply MF Markup (+0.00040)",
        value=st.session_state.default_apply_markup,
        key="toggle_default_apply_markup",
    )
    if default_apply_markup != st.session_state.default_apply_markup:
        st.session_state.default_apply_markup = default_apply_markup
        for key in list(st.session_state.keys()):
            if key.startswith("markup_"):
                st.session_state[key] = default_apply_markup

    debug_mode = st.toggle(
        "Enable Debug Mode",
        value=st.session_state.debug_mode,
        key="toggle_debug_mode",
    )
    st.session_state.debug_mode = debug_mode
    st.markdown("*Click Submit to calculate lease options.*")

# Control sidebar visibility
if 'sidebar_open' not in st.session_state:
    st.session_state.sidebar_open = True
st.sidebar.expanded = st.session_state.sidebar_open

if st.session_state.submitted and st.session_state.vin_input:
    vin_input = st.session_state.vin_input
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
                    st.subheader(f"{term}-Month Lease")
                    cols = st.columns(len(mileage_options))
                    for mileage, col in zip(mileage_options, cols):
                        with col:
                            row = matching_programs[matching_programs[term_col] == term].iloc[0]
                            mf_col = f"Tier {tier_num}"
                            if mf_col not in row or 'Residual' not in row or pd.isna(row[mf_col]) or pd.isna(row['Residual']):
                                st.info("This mileage and term combination is not available on the selected model.")
                                continue

                            base_residual = float(row['Residual'])
                            if mileage == 10000 and term >= 33:
                                adjusted_residual = base_residual + 0.01
                            elif mileage == 15000:
                                adjusted_residual = base_residual - 0.02
                            else:
                                adjusted_residual = base_residual

                            # Pre-compute initial payment for expander label
                            initial_selling_price = float(msrp)
                            initial_apply_markup = st.session_state.default_apply_markup
                            initial_mf = float(row[mf_col]) + (0.0004 if initial_apply_markup else 0.0)
                            initial_apply_cash = st.session_state.default_apply_cash
                            initial_cash = float(row["LeaseCash"]) if "LeaseCash" in row else 0.0
                            initial_total_ccr = money_down + (initial_cash if initial_apply_cash else 0.0)
                            initial_residual_value = round(float(msrp) * adjusted_residual, 2)
                            initial_payment_calc = calculate_base_and_monthly_payment(
                                S=initial_selling_price,
                                RES=initial_residual_value,
                                W=term,
                                F=initial_mf,
                                M=962.50,
                                Q=0,
                                B=initial_total_ccr,
                                K=0,
                                U=0,
                                tau=tax_rate
                            )
                            initial_monthly_payment = initial_payment_calc['Monthly Payment']

                            with st.expander(
                                f"Monthly Payment (w/ tax): {initial_monthly_payment}",
                                key=f"expander_{term}_{mileage}"
                            ) as expander:
                                selling_price = st.number_input("Selling Price ($)", value=float(msrp), step=100.0, key=f"sp_{term}_{mileage}")
                                apply_markup = st.toggle("Apply MF Markup (+0.00040)", value=st.session_state.default_apply_markup, key=f"markup_{term}_{mileage}")
                                mf = float(row[mf_col]) + (0.0004 if apply_markup else 0.0)
                                lease_cash = float(row["LeaseCash"]) if "LeaseCash" in row else 0.0
                                col1, col2 = st.columns(2)
                                with col1:
                                    apply_cash = st.toggle("Apply Lease Cash", value=st.session_state.default_apply_cash, key=f"applycash_{term}_{mileage}")
                                with col2:
                                    custom_cash = st.number_input("Cash ($)", value=lease_cash, step=100.0, key=f"cash_{term}_{mileage}", disabled=not apply_cash)
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
                                st.markdown(f"""
                                <div class="lease-details">
                                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem;">
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
                                            <p class="metric-label">Down Payment</p>
                                            <p class="metric-value">${money_down:,.2f}</p>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            if st.session_state.debug_mode:
                                st.markdown("**Debug Info**")
                                st.write({
                                    "Selling Price": f"${selling_price:,.2f}",
                                    "Residual Value": f"${residual_value:,.2f}",
                                    "Lease Term": f"{term} months",
                                    "Money Factor": f"{mf:.5f}",
                                    "Total CCR": f"${total_ccr:,.2f}",
                                    "Tax Rate": f"{tax_rate:.2%}",
                                    "Base Payment": f"${payment_calc['Base Payment']:,.2f}"
                                })
elif submit_button and not st.session_state.vin_input:
    st.error("Please enter a VIN before submitting.")
