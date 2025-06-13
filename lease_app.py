import streamlit as st
import pandas as pd
import os
import re

# Load lease and locator data
try:
    lease_data = pd.read_csv("All_Lease_Programs_Database.csv")
    lease_data.columns = lease_data.columns.str.strip()
except FileNotFoundError:
    st.error("Lease data file 'All_Lease_Programs_Database.csv' not found.")
    st.stop()

# Determine model column safely
model_column = None
if "MODEL" in lease_data.columns:
    model_column = "MODEL"
elif "ModelNumber" in lease_data.columns:
    model_column = "ModelNumber"
elif "MODEL #" in lease_data.columns:
    model_column = "MODEL #"
elif "MODEL NUMBER" in lease_data.columns:
    model_column = "MODEL NUMBER"
else:
    st.error("No valid model column (MODEL, ModelNumber, MODEL #, MODEL NUMBER) found in lease data.")
    st.stop()

lease_data[model_column] = (lease_data[model_column].astype(str)
                           .str.strip()
                           .str.upper()
                           .apply(lambda x: re.sub(r'[^\x20-\x7E]', '', x)))

excel_file = "Locator_Detail_20250605.xlsx"
if not os.path.exists(excel_file):
    st.error(f"Locator data file '{excel_file}' not found.")
    st.stop()

try:
    locator_data = pd.read_excel(excel_file)
    locator_data.columns = locator_data.columns.str.strip()
    locator_data["Vin"] = (locator_data["VIN"].astype(str)
                         .str.strip()
                         .str.upper()
                         .str.replace("\u200b", "")
                         .str.replace("\ufeff", ""))
except Exception as e:
    st.error(f"Failed to load locator data: {e}")
    st.stop()

try:
    county_df = pd.read_csv("County_Tax_Rates.csv")
    county_df["Dropdown_Label"] = county_df["County"] + " (" + county_df["Tax Rate"].astype(str) + "% )"
except FileNotFoundError:
    st.error("County tax rates file 'County_Tax_Rates.csv' not found.")
    st.stop()

def is_ev_phev(row: pd.Series) -> bool:
    desc = " ".join(str(row.get(col, "")) for col in ["Model", "Trim", "ModelDescription"]).lower()
    return any(k in desc for k in ["electric", "plug", "phev", "fuel cell"])

def run_ccr_balancing_loop(target_das, cap_cost, residual_value, term_months, mf, county_tax, q_value, tolerance=0.005, max_iterations=1000):
    min_ccr = 0.0
    max_ccr = target_das
    iteration = 0

    monthly_ltr_fee = round(q_value / term_months, 2)

    while iteration < max_iterations:
        iteration += 1
        ccr_guess = (min_ccr + max_ccr) / 2

        adj_cap_cost_loop = cap_cost - ccr_guess

        base_payment_loop = round(
            mf * (adj_cap_cost_loop + residual_value) +
            ((adj_cap_cost_loop - residual_value) / term_months),
            2
        )
        monthly_tax_loop = round(base_payment_loop * county_tax, 2)
        first_payment_loop = round(base_payment_loop + monthly_tax_loop + monthly_ltr_fee, 2)

        ccr_tax_loop = round(ccr_guess * county_tax, 2)

        total_das_loop = round(ccr_guess + ccr_tax_loop + first_payment_loop, 2)

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

def main():
    st.title("Lease Quote Calculator")

    vin = (st.text_input("Enter VIN:", help="VIN will be converted to uppercase for matching")
           .strip()
           .upper()
           .replace("\u200b", "")
           .replace("\ufeff", ""))
    tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])

    selected_county = st.selectbox(
        "Select County:",
        county_df["Dropdown_Label"],
        index=int(county_df[county_df["Dropdown_Label"].str.startswith("Marion")].index[0])
    )
    county_tax = county_df[county_df["Dropdown_Label"] == selected_county]["Tax Rate"].values[0] / 100

    money_down = st.number_input("Money Down ($)", value=0.0)

    if vin and tier:
        try:
            msrp_row = locator_data[locator_data["Vin"] == vin]
            if msrp_row.empty:
                st.error(f"VIN '{vin}' not found in locator file. Please check the VIN and try again.")
                return

            model_number = (msrp_row["ModelNumber"].iloc[0]
                           .strip()
                           .upper()
                           .replace("\u200b", "")
                           .replace("\ufeff", ""))
            model_number = re.sub(r'[^\x20-\x7E]', '', model_number)

            if model_number not in lease_data[model_column].values:
                st.error(f"No lease
