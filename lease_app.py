import streamlit as st
import pandas as pd
from lease_calculations import calculate_base_and_monthly_payment

st.title("Lease Quote Calculator")

# Load Data
lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
county_rates = pd.read_csv("County_Tax_Rates.csv")

# Input Section
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
            st.error("Missing required vehicle columns.")
            st.stop()

        model_number = vin_data["ModelNumber"].values[0]
        model = vin_data["Model"].values[0]
        trim = vin_data["Trim"].values[0]
        msrp = vin_data["MSRP"].values[0]

        st.markdown(f"**Model Number:** {model_number}<br>**Model:** {model}<br>**Trim:** {(trim or 'N/A')}<br>**MSRP:** ${msrp:,.2f}", unsafe_allow_html=True)

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
            tax_rate = county_rates[county_rates[county_column] == selected_county][rate_column].values[0] / 100

            for idx, row in matching_programs.iterrows():
                term_col = next((col for col in ["LeaseTerm", "Lease_Term", "Term"] if col in row), None)
                if not term_col:
                    continue

                term_months = row[term_col]
                mf_col = f"Tier {tier_num}"
                if mf_col not in row or pd.isna(row[mf_col]):
                    continue

                mf_to_use = float(row[mf_col])
                residual_percent = float(row["Residual"])
                residual_value = round(msrp * residual_percent, 2)
                default_lease_cash = row.get("LeaseCash", 0.0)

                with st.expander(f"Lease Quote for {term_months} Months"):
                    # Lease cash controls
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        toggle = st.checkbox("Apply Lease Cash", key=f"toggle_{idx}")
                    with col2:
                        st.write(f"(Available: ${default_lease_cash:,.2f})")
                    with col3:
                        if toggle:
                            edited_lease_cash = st.number_input(
                                "Lease Cash Amount",
                                value=default_lease_cash,
                                key=f"lease_cash_{idx}",
                                min_value=0.0,
                                step=100.0
                            )
                        else:
                            edited_lease_cash = 0

                    # Calculate lease_cash_to_use
                    lease_cash_to_use = edited_lease_cash if toggle else 0

                    # Calculate total CCR
                    total_ccr = money_down + rebates + lease_cash_to_use

                    # Calculate payment
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

                    # Prepare results dictionary
                    results = {
                        "Term": f"{term_months} months",
                        "Money Factor": f"{mf_to_use:.5f}",
                        "Residual Value": f"${residual_value:,.2f} ({residual_percent:.0%})",
                        "Cap Cost Reduction (CCR)": f"${payment_calc['Cap Cost Reduction']:,.2f}",
                        "Total Advance (TA)": f"${payment_calc['Total Advance']:,.2f}",
                        "Avg Monthly Depreciation (AMD)": f"${payment_calc['Average Monthly Depreciation']:,.2f}",
                        "Avg Lease Charge (ALC)": f"${payment_calc['Average Lease Charge']:,.2f}",
                        "Base Payment": f"${payment_calc['Base Payment']:,.2f}",
                        "Monthly Payment (w/ tax)": f"${payment_calc['Monthly Payment']:,.2f}",
                        "Total Sales Tax (over term)": f"${payment_calc['Total Sales Tax']:,.2f}",
                        "Lease Cash": f"Applied: ${lease_cash_to_use:,.2f}" if toggle else "Not Applied",
                        "Rebates/Credits": f"${rebates:,.2f}",
                        "Down Payment": f"${money_down:,.2f}",
                        "Inception Fees": f"${inception_fees:,.2f}",
                        "Non-cash CCR": f"${non_cash_ccr:,.2f}"
                    }

                    # Display the table
                    st.table(pd.DataFrame(results.items(), columns=["Item", "Value"]))
