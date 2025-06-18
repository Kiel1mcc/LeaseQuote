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
/* [styling omitted for brevity] */
</style>
""", unsafe_allow_html=True)

lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
county_rates = pd.read_csv("County_Tax_Rates.csv")

with st.sidebar:
    st.header("Lease Parameters")
    vin_input = st.text_input("Enter VIN:", value="", placeholder="Enter 17-digit VIN")
    selected_tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
    county_column = county_rates.columns[0]
    selected_county = st.selectbox("Select County:", county_rates[county_column])
    money_down = st.number_input("Down Payment ($)", min_value=0.0, value=0.0, step=100.0)

    st.subheader("Display Settings")
    show_money_factor = st.checkbox("Show Money Factor", value=True)
    show_residual = st.checkbox("Show Residual Value", value=True)
    show_monthly = st.checkbox("Show Monthly Payment", value=True)

    show_msrp = st.checkbox("Show MSRP", value=True)
    show_mileage = st.checkbox("Show Mileage", value=True)

    

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
        matching_programs = lease_programs[lease_programs[lease_col] == model_number]
        tier_num = int(selected_tier.split(" ")[1])
        tax_rate = county_rates[county_rates[county_column] == selected_county].iloc[0, 1] / 100

        mileage_options = [10000, 12000, 15000]
        term_col = next((col for col in matching_programs.columns if col.lower() in ["leaseterm", "lease_term", "term"]), None)
        rows_for_term = {term: matching_programs[matching_programs[term_col] == term] for term in sorted(matching_programs[term_col].dropna().unique())}

        st.markdown("<div class='lease-options-table'>", unsafe_allow_html=True)
        header_cols = st.columns([1] + [1] * len(mileage_options))
        header_cols[0].markdown("<div class='lease-term'></div>", unsafe_allow_html=True)
        for i, mileage in enumerate(mileage_options):
            header_cols[i + 1].markdown(f"<div class='mileage-header'>{mileage // 1000}K Miles</div>", unsafe_allow_html=True)

        for term in rows_for_term:
            row_group = rows_for_term[term]
            row_cols = st.columns([1] + [1] * len(mileage_options))
            row_cols[0].markdown(f"<div class='lease-term'>{term} Mo</div>", unsafe_allow_html=True)

            for i, mileage in enumerate(mileage_options):
                row = row_group.iloc[0]
                base_residual = float(row['Residual'])
                adjusted_residual = base_residual + 0.01 if mileage == 10000 else base_residual - 0.02 if mileage == 15000 else base_residual
                mf_col = f"Tier {tier_num}"
                lease_cash = float(row["LeaseCash"]) if "LeaseCash" in row else 0.0

                with row_cols[i + 1]:
                    monthly_placeholder = st.empty()
                    with st.expander("View Details"):
                        apply_markup = st.toggle("Remove MF Markup (-0.00040)", value=False, key=f"mf_markup_{term}_{mileage}")
                        apply_cash = st.toggle("Apply Lease Cash", value=False, key=f"apply_cash_{term}_{mileage}")
                        money_down_local = st.number_input("Down Payment ($)", min_value=0.0, value=money_down, step=100.0, key=f"cash_input_{term}_{mileage}")

                        mf = float(row[mf_col]) + (0.0 if apply_markup else -0.0004)
                        total_ccr = money_down_local + (lease_cash if apply_cash else 0.0)
                        selling_price = st.number_input(
                            "Selling Price ($)",
                            min_value=0.0,
                            value=float(msrp),
                            step=100.0,
                            key=f"selling_price_{term}_{mileage}"
                        )
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

                        monthly_placeholder.markdown(f"<div class='payment-value'>{title}</div>", unsafe_allow_html=True)

                        st.markdown(f"""
                        <div class="lease-details">
                            {f'''<div class="detail-item"><p class="metric-label">MSRP</p><p class="metric-value">${msrp:,.2f}</p></div>''' if show_msrp else ''}
                            {f'''<div class="detail-item"><p class="metric-label">Mileage</p><p class="metric-value">{mileage:,} mi/year</p></div>''' if show_mileage else ''}
                            {f'''<div class="detail-item"><p class="metric-label">Money Factor</p><p class="metric-value">{mf:.5f}</p></div>''' if show_money_factor else ''}
                            {f'''<div class="detail-item"><p class="metric-label">Residual Value</p><p class="metric-value">${residual_value:,.2f} ({adjusted_residual:.0%})</p></div>''' if show_residual else ''}
                            {f'''<div class="detail-item"><p class="metric-label">Monthly Payment</p><p class="metric-value">{payment_calc['Monthly Payment']}</p></div>''' if show_monthly else ''}
                        </div>
                        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
