import streamlit as st
import pandas as pd
import numpy as np
import datetime

# Helper function for lease payment calculation
def calculate_base_and_monthly_payment(S, RES, W, F, M, Q, B, tau):
    K = 0
    U = 0
    cap_cost = S + M - B
    depreciation = (cap_cost - RES) / W
    rent_charge = (cap_cost + RES) * F
    base_payment = depreciation + rent_charge
    tax = base_payment * tau
    monthly_payment = base_payment + tax

    return {
        "Base Payment": round(base_payment, 2),
        "Monthly Payment": round(monthly_payment, 2),
        "Cap Cost Reduction": round(B, 2)
    }

# Streamlit UI
st.title("Lease Quote Calculator")

lease_programs = pd.read_csv("Combined_Lease_Programs.csv")
vehicle_data = pd.read_excel("Inventory_Detail_20250527.xlsx")
county_rates = pd.read_csv("county_tax_rates.csv")

vin_input = st.text_input("Enter VIN:")
selected_tier = st.selectbox("Select Tier:", ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"])
selected_county = st.selectbox("Select County:", county_rates["Dropdown_Label"])
money_down = st.number_input("Money Down ($)", min_value=0.0, value=0.0)

if vin_input:
    vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
    if vin_data.empty:
        st.error("VIN not found in inventory.")
    else:
        model_number = vin_data["Model"].values[0]
        model_year = vin_data["MY"].values[0]
        msrp = vin_data["MSRP"].values[0]

        matching_programs = lease_programs[(lease_programs["Model_Year"] == model_year) &
                                           (lease_programs["Model_Number"] == model_number)]

        if matching_programs.empty:
            st.error("No lease entries found for this vehicle.")
        else:
            st.markdown(f"**MSRP:** ${msrp:,.2f}")
            tier_num = int(selected_tier.split(" ")[1])
            tax_rate = county_rates[county_rates["Dropdown_Label"] == selected_county]["Rate"].values[0]

            q_value = 47.50 + 15  # fixed fees

            for _, row in matching_programs.iterrows():
                term_months = row["Lease_Term"]
                mf_to_use = row["Money_Factor_Tier_" + str(tier_num)]
                residual_percent = row["Residual_Percentage"]
                residual_value = round(msrp * residual_percent, 2)
                lease_cash = row["Lease_Cash"]

                # Placeholder CCR calculation
                total_ccr = money_down + lease_cash

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
