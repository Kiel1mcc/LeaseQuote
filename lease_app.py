import streamlit as st
import pandas as pd
import numpy as np
import datetime

# Helper function for lease payment calculation
def calculate_base_and_monthly_payment(S, RES, W, F, M, Q, B, K, U, tau):
    # Step 2: Total Advance (TA)
    TA = S + Q + K + (F * (S + M - B - U + RES)) * W + M - B - U

    # Step 3: Average Monthly Depreciation (AMD)
    AMD = (TA - RES) / W

    # Step 4: Average Lease Charge (ALC)
    ALC = F * (TA + RES)

    # Step 5: Monthly Payment = AMD + ALC
    monthly_payment = AMD + ALC

    # Base Payment (before tax)
    base_payment = monthly_payment / (1 + tau)

    # Total Sales Tax over lease term
    total_sales_tax = monthly_payment * W - base_payment * W

    return {
        "Base Payment": round(base_payment, 2),
        "Monthly Payment": round(monthly_payment, 2),
        "Cap Cost Reduction": round(B + U, 2),
        "Average Monthly Depreciation": round(AMD, 2),
        "Average Lease Charge": round(ALC, 2),
        "Total Advance": round(TA, 2),
        "Total Sales Tax": round(total_sales_tax, 2)
    }

# Streamlit UI
st.title("Lease Quote Calculator")

# Input mode selection
input_mode = st.radio("Select Input Mode:", ["VIN Lookup", "Custom Inputs"])

# Load data
lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
county_rates = pd.read_csv("County_Tax_Rates.csv")

if input_mode == "VIN Lookup":
    vin_input = st.text_input("Enter VIN:")
    selected_tier = st.selectbox("Select Tier:", ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"])
    county_column = county_rates.columns[0]
    selected_county = st.selectbox("Select County:", county_rates[county_column])
    rebates = st.number_input("Rebates/Credits ($)", min_value=0.0, value=0.0)
    money_down = st.number_input("Money Down ($)", min_value=0.0, value=0.0)
    inception_fees = st.number_input("Lease Inception Fees ($)", min_value=0.0, value=0.0)
    non_cash_ccr = st.number_input("Non-cash CCR ($)", min_value=0.0, value=0.0)

    if vin_input:
        vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
        if vin_data.empty:
            st.error("VIN not found in inventory.")
        else:
            if not all(col in vin_data.columns for col in ["ModelNumber", "Model", "Trim", "MSRP"]):
                st.error("Missing required columns. Columns found: " + ", ".join(vin_data.columns))
                st.stop()

            model_number = vin_data["ModelNumber"].values[0]
            model = vin_data["Model"].values[0]
            trim = vin_data["Trim"].values[0]
            msrp = vin_data["MSRP"].values[0]

            st.markdown(f"**Model Number:** {model_number}<br>**Model:** {model}<br>**Trim:** {trim}<br>**MSRP:** ${msrp:,.2f}", unsafe_allow_html=True)

            lease_col_match = [col for col in lease_programs.columns if col.strip().lower() == "modelnumber"]
            if not lease_col_match:
                st.error("ModelNumber column not found in lease program file. Columns available: " + ", ".join(lease_programs.columns))
                st.stop()

            lease_col = lease_col_match[0]
            matching_programs = lease_programs[lease_programs[lease_col] == model_number]

            if matching_programs.empty:
                st.error("No lease entries found for this vehicle.")
            else:
                tier_num = int(selected_tier.split(" ")[1])
                rate_column = "Rate" if "Rate" in county_rates.columns else county_rates.columns[-1]
                tax_rate = county_rates[county_rates[county_column] == selected_county][rate_column].values[0] / 100
                q_value = 47.50 + 15  # fixed fees

                for _, row in matching_programs.iterrows():
                    term_months = None
                    for possible_term_col in ["LeaseTerm", "Lease_Term", "Term"]:
                        if possible_term_col in row:
                            term_months = row[possible_term_col]
                            break

                    if term_months is None:
                        st.error("Lease term column not found in lease program entry.")
                        continue

                    mf_col = f"Tier {tier_num}"
                    if mf_col not in row:
                        st.error(f"Missing money factor column '{mf_col}' in lease program.")
                        continue

                    mf_to_use = row[mf_col]
                    residual_percent = row["Residual"]
                    residual_value = round(msrp * residual_percent, 2)
                    lease_cash = row["LeaseCash"]

                    # CCR calculation
                    fw = round(F := mf_to_use * term_months, 6)
                    smu_res_plus = round(msrp + 900 + residual_value, 6)
                    smu_res_minus = round(msrp + 900 - residual_value, 6)

                    total_money_down = money_down + rebates + lease_cash
                    top = round(
                        total_money_down
                        - (mf_to_use * (msrp + 900 + q_value + tax_rate * (fw * smu_res_plus + smu_res_minus) - 0 + residual_value))
                        + ((msrp + 900 + q_value + tax_rate * (fw * smu_res_plus + smu_res_minus) - 0 - residual_value) / term_months), 6
                    )
                    bottom = round((1 + tax_rate) * (1 - ((mf_to_use + 1 / term_months)) - tax_rate * mf_to_use * (1 + mf_to_use * term_months)), 4)
                    total_ccr = round(top / bottom, 2)

                    payment_calc = calculate_base_and_monthly_payment(
                        S=msrp,
                        RES=residual_value,
                        W=term_months,
                        F=mf_to_use,
                        M=900,
                        Q=q_value,
                        B=total_ccr,
                        K=inception_fees,
                        U=non_cash_ccr,
                        tau=tax_rate
                    )

                    st.markdown(f"""
                    ### {term_months}-Month Lease
                    **Money Factor:** {mf_to_use:.5f}  
                    **Residual Value:** ${residual_value:,.2f} ({residual_percent:.0%})  
                    **Cap Cost Reduction (CCR):** ${payment_calc['Cap Cost Reduction']:,.2f}  
                    **Total Advance (TA):** ${payment_calc['Total Advance']:,.2f}  
                    **Average Monthly Depreciation (AMD):** ${payment_calc['Average Monthly Depreciation']:,.2f}  
                    **Average Lease Charge (ALC):** ${payment_calc['Average Lease Charge']:,.2f}  
                    **Base Payment:** ${payment_calc['Base Payment']:,.2f}  
                    **Monthly Payment (w/ tax):** ${payment_calc['Monthly Payment']:,.2f}  
                    **Total Sales Tax (over term):** ${payment_calc['Total Sales Tax']:,.2f}  
                    **Lease Cash Applied:** ${lease_cash:,.2f}  
                    **Rebates/Credits:** ${rebates:,.2f}  
                    **Down Payment:** ${money_down:,.2f}  
                    **Inception Fees:** ${inception_fees:,.2f}  
                    **Non-cash CCR:** ${non_cash_ccr:,.2f}  
                    ---
                    """)
else:
    # Custom Inputs
    selling_price = st.number_input("Selling Price ($)", min_value=0.0, value=25425.0)
    residual_value = st.number_input("Residual Value ($)", min_value=0.0, value=15255.0)
    lease_term = st.number_input("Lease Term (months)", min_value=1, value=36)
    money_factor = st.number_input("Money Factor", min_value=0.0, value=0.00296, format="%.5f")
    taxable_fees = st.number_input("Taxable Fees ($)", min_value=0.0, value=900.0)
    non_taxable_fees = st.number_input("Non-taxable Fees ($)", min_value=0.0, value=62.5)
    rebates = st.number_input("Rebates/Credits ($)", min_value=0.0, value=3000.0)
    inception_fees = st.number_input("Lease Inception Fees ($)", min_value=0.0, value=0.0)
    non_cash_ccr = st.number_input("Non-cash CCR ($)", min_value=0.0, value=0.0)
    county_column = county_rates.columns[0]
    selected_county = st.selectbox("Select County:", county_rates[county_column])
    rate_column = "Rate" if "Rate" in county_rates.columns else county_rates.columns[-1]
    tax_rate = county_rates[county_rates[county_column] == selected_county][rate_column].values[0] / 100

    # Simplified CCR for custom inputs (approximation)
    total_ccr = rebates + non_cash_ccr

    payment_calc = calculate_base_and_monthly_payment(
        S=selling_price,
        RES=residual_value,
        W=lease_term,
        F=money_factor,
        M=taxable_fees,
        Q=non_taxable_fees,
        B=total_ccr,
        K=inception_fees,
        U=non_cash_ccr,
        tau=tax_rate
    )

    st.markdown(f"""
    ### {lease_term}-Month Lease (Custom)
    **Selling Price:** ${selling_price:,.2f}  
    **Residual Value:** ${residual_value:,.2f}  
    **Money Factor:** {money_factor:.5f}  
    **Cap Cost Reduction (CCR):** ${payment_calc['Cap Cost Reduction']:,.2f}  
    **Total Advance (TA):** ${payment_calc['Total Advance']:,.2f}  
    **Average Monthly Depreciation (AMD):** ${payment_calc['Average Monthly Depreciation']:,.2f}  
    **Average Lease Charge (ALC):** ${payment_calc['Average Lease Charge']:,.2f}  
    **Base Payment:** ${payment_calc['Base Payment']:,.2f}  
    **Monthly Payment (w/ tax):** ${payment_calc['Monthly Payment']:,.2f}  
    **Total Sales Tax (over term):** ${payment_calc['Total Sales Tax']:,.2f}  
    **Rebates/Credits:** ${rebates:,.2f}  
    **Inception Fees:** ${inception_fees:,.2f}  
    **Non-cash CCR:** ${non_cash_ccr:,.2f}  
    """)
