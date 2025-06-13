import streamlit as st
import pandas as pd
import re

# Load data files with error handling
try:
    lease_data = pd.read_csv("All_Lease_Programs_Database.csv")
    lease_data.columns = lease_data.columns.str.strip()
except FileNotFoundError:
    st.error("Lease data file 'All_Lease_Programs_Database.csv' not found.")
    st.stop()

# Determine the model column dynamically
model_column = None
for col in ["ModelNumber", "MODEL", "MODEL #", "MODEL NUMBER"]:
    if col in lease_data.columns:
        model_column = col
        break
if model_column is None:
    st.error("No valid model column found in lease data.")
    st.stop()

# Clean the model column
lease_data[model_column] = (lease_data[model_column].astype(str)
                           .str.strip()
                           .str.upper()
                           .apply(lambda x: re.sub(r'[^\x20-\x7E]', '', x)))

try:
    county_df = pd.read_csv("County_Tax_Rates.csv")
    county_df.columns = county_df.columns.str.strip()
    county_df["Dropdown_Label"] = county_df["County"] + " (" + county_df["Tax Rate"].astype(str) + "%)"
except FileNotFoundError:
    st.error("County tax rates file 'County_Tax_Rates.csv' not found.")
    st.stop()

try:
    locator_data = pd.read_excel("Locator_Detail_20250605.xlsx", dtype={"MSRP": str})
    locator_data.columns = locator_data.columns.str.strip()
    locator_data["VIN"] = (locator_data["VIN"].astype(str)
                         .str.strip()
                         .str.upper()
                         .str.replace("\u200b", "")
                         .str.replace("\ufeff", ""))
except FileNotFoundError:
    st.error("Locator data file 'Locator_Detail_20250605.xlsx' not found.")
    st.stop()

def run_ccr_balancing_loop(target_das, msrp, lease_cash, residual_value, term_months, mf, county_tax, q_value, tolerance=0.005, max_iterations=1000):
    min_ccr = 0.0
    max_ccr = target_das
    iteration = 0

    fixed_fees = 250.00 + 650.00 + 15.00 + 47.50
    cap_cost = msrp - lease_cash

    while iteration < max_iterations:
        iteration += 1
        ccr_guess = (min_ccr + max_ccr) / 2

        adj_cap_cost_loop = cap_cost - ccr_guess

        monthly_depreciation = (adj_cap_cost_loop - residual_value) / term_months
        monthly_rent_charge = (adj_cap_cost_loop + residual_value) * mf
        base_payment_loop = round(monthly_depreciation + monthly_rent_charge, 2)

        monthly_tax_loop = round(base_payment_loop * county_tax, 2)

        # CDK-style First Payment calculation: full Q fee + tax up front
        ltr_fee_upfront = 62.50
        ltr_fee_tax = round(ltr_fee_upfront * county_tax, 2)

        first_payment_loop = round(base_payment_loop + monthly_tax_loop + ltr_fee_upfront + ltr_fee_tax, 2)

        ccr_tax_loop = round(ccr_guess * county_tax, 2)

        total_das_loop = round(ccr_guess + ccr_tax_loop + first_payment_loop + fixed_fees, 2)

        if abs(total_das_loop - target_das) <= tolerance:
            break

        if total_das_loop > target_das:
            max_ccr = ccr_guess
        else:
            min_ccr = ccr_guess

    return {
        "CCR": round(ccr_guess, 2),
        "CCR_Tax": ccr_tax_loop,
        "First_Payment": first_payment_loop,
        "Total_DAS": total_das_loop,
        "Iterations": iteration
    }
