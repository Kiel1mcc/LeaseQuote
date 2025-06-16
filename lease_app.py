import streamlit as st
import pandas as pd
import numpy as np
import datetime

# Helper function for lease payment calculation
def calculate_base_and_monthly_payment(S, RES, W, F, M, Q, B, tau):
    # Step 1: Cap Cost Calculation (already pre-calculated into B as Cap Cost Reduction)
    K = 0
    U = 0

    # Step 2: Total Advance (TA)
    TA = S + Q + (F * (S + M - B + RES)) * W + M - B

    # Step 3: Average Monthly Depreciation (AMD)
    AMD = (TA - RES) / W

    # Step 4: Average Lease Charge (ALC)
    ALC = F * (TA + RES)

    # Step 5: Monthly Payment = AMD + ALC
    monthly_payment = AMD + ALC

    # Base Payment is treated here as same as monthly base before tax if needed
    base_payment = monthly_payment / (1 + tau)  # remove tax to isolate base

    return {
        "Base Payment": round(base_payment, 2),
        "Monthly Payment": round(monthly_payment, 2),
        "Cap Cost Reduction": round(B, 2)
    }

# Streamlit UI
st.title("Lease Quote Calculator")

lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
county_rates = pd.read_csv("County_Tax_Rates.csv")

vin_input = st.text_input("Enter VIN:")
selected_tier = st.selectbox("Select Tier:", ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"])

county_column = county_rates.columns[0]  # fallback to first column
selected_county = st.selectbox("Select County:", county_rates[county_column])

money_down = st.number_input("Money Down ($)", min_value=0.0, value=0.0)

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
            tax_rate = county_rates[county_rates[county_column] == selected_county][rate_column].values[0]
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

                # Updated CCR calculation based on Excel breakdown
                top = money_down
                fw = round(mf_to_use * term_months, 6)
                smu_res = round(msrp + 900 - 0 + residual_value, 6)
                smu_res_diff = round(msrp + 900 - 0 - residual_value, 6)

                top -= mf_to_use * (msrp + 900 + q_value + tax_rate * (fw * smu_res + smu_res_diff) - 0 + residual_value)
                top += (msrp + 900 + q_value + tax_rate * (fw * smu_res + smu_res_diff) - 0 - residual_value) / term_months

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
                    tau=tax_rate
                )

                st.markdown(f"""
                ### {term_months}-Month Lease
                **Base Payment:** ${payment_calc['Base Payment']:.2f}  
                **Monthly Payment (w/ tax):** ${payment_calc['Monthly Payment']:.2f}  
                **Cap Cost Reduction:** ${payment_calc['Cap Cost Reduction']:.2f}  
                **Lease Cash Applied:** ${lease_cash:,.2f}  
                **Down Payment:** ${money_down:,.2f}  
                ---
                """)
