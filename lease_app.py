
import streamlit as st
import pandas as pd
from lease_calculations import calculate_ccr_full, calculate_payment_from_ccr

st.set_page_config(page_title="Lease Quote Tool", layout="wide")

# Load data files
lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
county_rates = pd.read_csv("County_Tax_Rates.csv")

# Sidebar inputs
with st.sidebar:
    st.header("Lease Parameters")
    vin_input = st.text_input("Enter VIN:", "")
    selected_tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
    selected_county = st.selectbox("Select County:", county_rates.iloc[:, 0])
    trade_value = st.number_input("Trade Value ($)", min_value=0.0, value=0.0, step=100.0)
    default_money_down = st.number_input("Default Down Payment ($)", min_value=0.0, value=0.0, step=100.0)

# VIN Lookup
if vin_input:
    vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
    if vin_data.empty:
        st.error("VIN not found.")
    else:
        vehicle = vin_data.iloc[0]
        msrp = vehicle["MSRP"]
        model_number = vehicle["ModelNumber"]

        st.markdown(f"### Vehicle: {vehicle['Year']} {vehicle['Make']} {vehicle['Model']} {vehicle['Trim']}")

        matching_programs = lease_programs[lease_programs["ModelNumber"] == model_number]
        tier_num = int(selected_tier.split(" ")[1])
        tax_rate = county_rates[county_rates.iloc[:, 0] == selected_county].iloc[0, 1] / 100

        mileage_options = [10000, 12000, 15000]
        lease_terms = sorted(matching_programs["LeaseTerm"].dropna().unique())

        for term in lease_terms:
            term_group = matching_programs[matching_programs["LeaseTerm"] == term]
            st.subheader(f"{term}-Month Lease")

            for mileage in mileage_options:
                residual_row = term_group.iloc[0]
                base_residual = float(residual_row["Residual"])
                adjusted_residual = base_residual + 0.01 if mileage == 10000 else base_residual - 0.02 if mileage == 15000 else base_residual
                residual_value = round(msrp * adjusted_residual, 2)

                mf_col = f"Tier {tier_num}"
                money_factor = float(residual_row[mf_col])
                available_lease_cash = float(residual_row.get("LeaseCash", 0.0))

                st.markdown(f"**Mileage: {mileage:,} / yr**")
                selling_price = st.number_input(
                    f"Selling Price ($) — {term} mo / {mileage:,} mi",
                    value=msrp,
                    key=f"price_{term}_{mileage}"
                )

                lease_cash_used = st.number_input(
                    f"Lease Cash Used ($) — Max: ${available_lease_cash:,.2f}",
                    min_value=0.0,
                    max_value=available_lease_cash,
                    value=available_lease_cash,
                    step=1.0,
                    key=f"lease_cash_{term}_{mileage}"
                )

                money_down_slider = st.slider(
                    f"Adjust Down Payment ($) — {term} mo / {mileage:,} mi",
                    min_value=0,
                    max_value=5000,
                    value=int(default_money_down),
                    step=50,
                    key=f"down_{term}_{mileage}"
                )

                credits = money_down_slider + lease_cash_used
                ccr_result = calculate_ccr_full(
                    selling_price=selling_price,
                    trade_value=trade_value,
                    credits=credits,
                    inception_fees=0,
                    non_cash_ccr=0,
                    taxable_fees=962.50,
                    nontaxable_fees=0.0,
                    tax_rate=tax_rate,
                    money_factor=money_factor,
                    term_months=term,
                    residual_value=residual_value
                )

                payment = calculate_payment_from_ccr(
                    selling_price=selling_price,
                    cap_cost_reduction=ccr_result["Recalculated_CCR"],
                    residual_value=residual_value,
                    term_months=term,
                    money_factor=money_factor,
                    tax_rate=tax_rate
                )

                st.markdown(f"**Monthly Payment: ${payment['Monthly Payment']:.2f}**")
                st.markdown(f"*Base: ${payment['Base Payment']:.2f}, Tax: ${payment['Total Sales Tax']:.2f}, CCR: ${ccr_result['Recalculated_CCR']:.2f}*")
