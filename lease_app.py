import streamlit as st
import pandas as pd
import numpy as np
import os

# Set page configuration must be the first Streamlit command
st.set_page_config(page_title="Lease Quote Calculator", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    .main {background-color: #f9f9f9;}
    .sidebar .stTextInput, .sidebar .stSelectbox, .sidebar .stNumberInput {margin-bottom: 1rem;}
    .stButton>button {background-color: #0066cc; color: white; border-radius: 5px;}
    .stButton>button:hover {background-color: #0055b3;}
    .vehicle-info {background-color: #e6f0fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;}
    .lease-details {background-color: #ffffff; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    .error {color: #d32f2f; font-weight: bold;}
    h1 {color: #003087; font-size: 2rem;}
    h3 {color: #003087; margin-top: 1.5rem;}
    .metric-label {font-size: 0.9rem; color: #555;}
    .metric-value {font-size: 1.1rem; font-weight: bold; color: #003087;}
</style>
""", unsafe_allow_html=True)

# Title
st.title("Lease Quote Calculator")

# Load Data
try:
    lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
    vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
    county_rates = pd.read_csv("County_Tax_Rates.csv")
except FileNotFoundError:
    st.error("Required data files are missing. Please ensure all files are available.")
    st.stop()

# Sidebar for Inputs
with st.sidebar:
    st.header("Lease Parameters")
    vin_input = st.text_input("Enter VIN:", value="")
    selected_tier = st.selectbox("Select Tier:", ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5", "Tier 6", "Tier 7", "Tier 8"])
    county_column = county_rates.columns[0]
    selected_county = st.selectbox("Select County:", county_rates[county_column])
    rebates = st.number_input("Rebates/Credits ($)", min_value=0.0, value=0.0, step=100.0)
    money_down = st.number_input("Money Down ($)", min_value=0.0, value=0.0, step=100.0)
    inception_fees = st.number_input("Lease Inception Fees ($)", min_value=0.0, value=0.0, step=100.0)
    non_cash_ccr = st.number_input("Non-cash CCR ($)", min_value=0.0, value=0.0, step=100.0)

# Main Content
def process_lease_data():
    # Lazy import to avoid circular import issues
    from lease_calculations import calculate_base_and_monthly_payment
    
    if vin_input:
        vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
        if vin_data.empty:
            st.error("VIN not found in inventory. Please check the VIN and try again.")
        else:
            model_number = vin_data["ModelNumber"].values[0]
            model = vin_data["Model"].values[0]
            trim = vin_data["Trim"].values[0]
            msrp = vin_data["MSRP"].values[0]

            # Display Vehicle Information
            with st.container():
                st.markdown("### Vehicle Information")
                st.markdown(f"""
                <div class="vehicle-info">
                    <p><b>Model Number:</b> {model_number}</p>
                    <p><b>Model:</b> {model}</p>
                    <p><b>Trim:</b> {trim}</p>
                    <p><b>MSRP:</b> ${msrp:,.2f}</p>
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
                if tier_num < 1 or tier_num > 8:
                    st.error("Invalid tier selected. Please choose a tier between 1 and 8.")
                    st.stop()

                rate_column = "Rate" if "Rate" in county_rates.columns else county_rates.columns[-1]
                tax_rate = county_rates[county_rates[county_column] == selected_county][rate_column].values[0] / 100

                # Display Lease Options
                st.markdown("### Lease Options")
                for _, row in matching_programs.iterrows():
                    term_col = next((col for col in ["LeaseTerm", "Lease_Term", "Term"] if col in row), None)
                    if not term_col:
                        continue

                    term_months = row[term_col]
                    mf_col = f"Tier {tier_num}"
                    if mf_col not in row or pd.isna(row[mf_col]):
                        st.warning(f"No money factor data available for {selected_tier} for this term.")
                        continue

                    mf_to_use = float(row[mf_col])
                    residual_percent = float(row["Residual"])
                    residual_value = round(msrp * residual_percent, 2)
                    lease_cash = float(row["LeaseCash"]) if "LeaseCash" in row else 0.0

                    total_ccr = money_down + rebates + lease_cash

                    payment_calc = calculate_base_and_monthly_payment(
                        S=msrp,
                        RES=residual_value,
                        W=term_months,
                        F=mf_to_use,
                        M=962.50,
                        Q=0,
                        B=total_ccr,
                        K=inception_fees,
                        U=non_cash_ccr,
                        tau=tax_rate
                    )

                    # Debug output of payment_calc
                    st.write(f"Debug - payment_calc for {term_months}-month lease: {payment_calc}")

                    # Display Lease Details with string parsing
                    with st.container():
                        st.markdown(f"#### {term_months}-Month Lease")
                        required_keys = ['Cap Cost Reduction', 'Total Advance', 'Average Monthly Depreciation', 'Average Lease Charge', 'Base Payment', 'Monthly Payment', 'Total Sales Tax']
                        if not all(key in payment_calc for key in required_keys):
                            missing_keys = [key for key in required_keys if key not in payment_calc]
                            st.error(f"Calculation error for {term_months}-month lease. Missing keys: {missing_keys}. Please check input data.")
                            continue
                        # Parse string values to extract numbers
                        safe_payment_calc = {}
                        for key in required_keys:
                            value = payment_calc[key].replace('$', '').replace(',', '')
                            safe_payment_calc[key] = float(value) if value else 0.0
                        st.markdown(f"""
                        <div class="lease-details">
                            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                                <div>
                                    <p class="metric-label">Money Factor</p>
                                    <p class="metric-value">{mf_to_use:.5f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Residual Value</p>
                                    <p class="metric-value">${residual_value:,.2f} ({residual_percent:.0%})</p>
                                </div>
                                <div>
                                    <p class="metric-label">Cap Cost Reduction (CCR)</p>
                                    <p class="metric-value">${safe_payment_calc['Cap Cost Reduction']:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Total Advance (TA)</p>
                                    <p class="metric-value">${safe_payment_calc['Total Advance']:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Average Monthly Depreciation (AMD)</p>
                                    <p class="metric-value">${safe_payment_calc['Average Monthly Depreciation']:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Average Lease Charge (ALC)</p>
                                    <p class="metric-value">${safe_payment_calc['Average Lease Charge']:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Base Payment</p>
                                    <p class="metric-value">${safe_payment_calc['Base Payment']:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Monthly Payment (w/ tax)</p>
                                    <p class="metric-value">${safe_payment_calc['Monthly Payment']:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Total Sales Tax (over term)</p>
                                    <p class="metric-value">${safe_payment_calc['Total Sales Tax']:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Lease Cash Applied</p>
                                    <p class="metric-value">${lease_cash:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Rebates/Credits</p>
                                    <p class="metric-value">${rebates:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Down Payment</p>
                                    <p class="metric-value">${money_down:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Inception Fees</p>
                                    <p class="metric-value">${inception_fees:,.2f}</p>
                                </div>
                                <div>
                                    <p class="metric-label">Non-cash CCR</p>
                                    <p class="metric-value">${non_cash_ccr:,.2f}</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

if __name__ == "__main__":
    process_lease_data()
