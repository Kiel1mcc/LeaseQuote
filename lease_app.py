import streamlit as st
import pandas as pd
from lease_calculations import calculate_base_and_monthly_payment

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
    }
    .stTextInput>div>input {
        border: 2px solid #4CAF50;
        border-radius: 4px;
    }
    .streamlit-expander {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .gray-text {
        color: gray;
        font-size: 0.9em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Lease Quote Calculator")

# Load Data
lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
county_rates = pd.read_csv("County_Tax_Rates.csv")

# Initialize session state for calculation
if 'calculated' not in st.session_state:
    st.session_state.calculated = False

# Inputs
st.subheader("Vehicle and Lease Information")
vin_input = st.text_input("Enter VIN:")
selected_tier = st.selectbox("Select Tier:", ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"])
county_column = county_rates.columns[0]
selected_county = st.selectbox("Select County:", county_rates[county_column])
cash_down = st.number_input("Cash Down ($)", min_value=0.0, value=0.0)
apply_rebates = st.checkbox("Apply Rebates", help="Check to apply available rebates to the lease calculation.")

# Calculate button
if st.button("Calculate Lease Quote"):
    st.session_state.calculated = True

# Perform calculations only if calculated is True and VIN is provided
if st.session_state.calculated and vin_input:
    vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
    if vin_data.empty:
        st.error("VIN not found in inventory. Please check the VIN and try again.")
    else:
        if not all(col in vin_data.columns for col in ["ModelNumber", "Model", "Trim", "MSRP"]):
            st.error("Missing required vehicle columns.")
            st.stop()

        model_number = vin_data["ModelNumber"].values[0]
        model = vin_data["Model"].values[0]
        trim = vin_data["Trim"].values[0]
        msrp = vin_data["MSRP"].values[0]

        # Display vehicle information in a styled box
        st.markdown(f"""
        <div class='vehicle-info' style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
            <strong>Model Number:</strong> {model_number}<br>
            <strong>Model:</strong> {model}<br>
            <strong>Trim:</strong> {trim}<br>
            <strong>MSRP:</strong> ${msrp:,.2f}
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
            tax_rate = county_rates[county_rates[county_column] == selected_county][rate_column].values[0] / 100

            for _, row in matching_programs.iterrows():
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
                lease_cash = float(row["LeaseCash"]) if "LeaseCash" in row else 0.0
                rebates = float(row["Rebates"]) if "Rebates" in row else 0.0

                with st.expander(f"{term_months}-Month Lease"):
                    # Lease cash toggle with dynamic label and grayed-out available amount
                    col1, col2, col3 = st.columns([1, 2, 2])
                    with col1:
                        apply_lease_cash = st.checkbox("", key=f"toggle_{term_months}")
                    with col2:
                        if apply_lease_cash:
                            st.write("Remove Lease Cash")
                        else:
                            st.write("Apply Lease Cash")
                    with col3:
                        st.markdown(f"<span class='gray-text'>(Available: ${lease_cash:,.2f})</span>", unsafe_allow_html=True)

                    if apply_lease_cash:
                        lease_cash_to_use = st.number_input("Lease Cash Amount", value=lease_cash, key=f"lease_cash_{term_months}", min_value=0.0)
                    else:
                        lease_cash_to_use = 0.0

                    rebates_to_use = rebates if apply_rebates else 0.0

                    # Calculate total CCR including Cash Down
                    total_ccr = cash_down + rebates_to_use + lease_cash_to_use

                    payment_calc = calculate_base_and_monthly_payment(
                        S=msrp,
                        RES=residual_value,
                        W=term_months,
                        F=mf_to_use,
                        M=962.50,
                        Q=0,
                        B=total_ccr,
                        K=0,  # Lease Inception Fees removed
                        U=0,  # Non-cash CCR removed
                        tau=tax_rate
                    )

                    # Display key metric: Monthly Payment
                    st.write(f"## Monthly Payment: ${payment_calc['Monthly Payment']:,.2f}")

                    # Display other metrics in columns
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Money Factor", f"{mf_to_use:.5f}")
                        st.metric("Residual Value", f"${residual_value:,.2f} ({residual_percent:.0%})")
                        st.metric("Cap Cost Reduction (CCR)", f"${payment_calc['Cap Cost Reduction']:,.2f}")
                    with col2:
                        st.metric("Total Advance (TA)", f"${payment_calc['Total Advance']:,.2f}")
                        st.metric("Avg Monthly Depreciation (AMD)", f"${payment_calc['Average Monthly Depreciation']:,.2f}")
                        st.metric("Avg Lease Charge (ALC)", f"${payment_calc['Average Lease Charge']:,.2f}")
                    with col3:
                        st.metric("Base Payment", f"${payment_calc['Base Payment']:,.2f}")
                        st.metric("Total Sales Tax (over term)", f"${payment_calc['Total Sales Tax']:,.2f}")
                        st.metric("Down Payment", f"${cash_down:,.2f}")

                    # Additional information
                    st.write(f"**Lease Cash Applied:** {'Yes' if apply_lease_cash else 'No'}")
                    st.write(f"**Rebates Applied:** {'Yes' if apply_rebates else 'No'}")
