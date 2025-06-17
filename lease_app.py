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

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "main"

if 'settings' not in st.session_state:
    st.session_state.settings = {
        "default_county": "Adams",  # Replace with an actual default county
        "default_tier": "Tier 1",
        "default_apply_rebates": False,
        "auto_apply_lease_cash": False,
        "money_factor_markup": 0.0,
        "enable_debug": False
    }

# Load Data
lease_programs = pd.read_csv("All_Lease_Programs_Database.csv")
vehicle_data = pd.read_excel("Locator_Detail_20250605.xlsx")
county_rates = pd.read_csv("County_Tax_Rates.csv")
county_column = county_rates.columns[0]

# ----------------------
# Data validation helpers
# ----------------------

def validate_columns(df, required_cols, name):
    """Check that required columns are present in a DataFrame."""
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"{name} is missing required columns: {', '.join(missing)}")
        return False
    return True

data_valid = True

if not validate_columns(vehicle_data, ["VIN", "ModelNumber", "Model", "Trim", "MSRP"], "Vehicle data"):
    data_valid = False

if not validate_columns(lease_programs, ["ModelNumber", "Residual"], "Lease program data"):
    data_valid = False

if not validate_columns(county_rates, [county_column], "County tax rates"):
    data_valid = False

if st.session_state.page == "main":
    st.title("Lease Quote Calculator")

    if not data_valid:
        st.warning("Unable to run calculator due to missing data columns.")
    else:
        # Inputs with defaults from settings
        st.subheader("Vehicle and Lease Information")
        vin_input = st.text_input("Enter VIN:")
        tiers = ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"]
        selected_tier = st.selectbox(
            "Select Tier:",
            tiers,
            index=tiers.index(st.session_state.settings["default_tier"])
        )
        counties = county_rates[county_column].tolist()
        selected_county = st.selectbox(
            "Select County:",
            counties,
            index=counties.index(st.session_state.settings["default_county"]) if st.session_state.settings["default_county"] in counties else 0
        )
        cash_down = st.number_input("Cash Down ($)", min_value=0.0, value=0.0)
        apply_rebates = st.checkbox(
            "Apply Rebates",
            value=st.session_state.settings["default_apply_rebates"],
            help="Check to apply available rebates to the lease calculation."
        )

        # Calculate button
        if st.button("Calculate Lease Quote"):
            st.session_state.calculated = True

    # Perform calculations
    if 'calculated' in st.session_state and st.session_state.calculated and vin_input:
        vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
        if vin_data.empty:
            st.error("VIN not found in inventory. Please check the VIN and try again.")
        else:
            if not all(col in vin_data.columns for col in ["ModelNumber", "Model", "Trim", "MSRP"]):
                st.error("Missing required vehicle columns.")
            else:
                model_number = vin_data["ModelNumber"].values[0]
                model = vin_data["Model"].values[0]
                trim = vin_data["Trim"].values[0]
                msrp = vin_data["MSRP"].values[0]
                if cash_down > msrp:
                    st.warning("Cash down exceeds MSRP. Using MSRP as maximum.")
                    cash_down = msrp

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
            else:
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
                        col1, col2, col3 = st.columns([1, 2, 2])
                        with col1:
                            apply_lease_cash = st.checkbox("", key=f"toggle_{term_months}", value=st.session_state.settings["auto_apply_lease_cash"])
                        with col2:
                            if apply_lease_cash:
                                st.write("Remove Lease Cash")
                            else:
                                st.write("Apply Lease Cash")
                        with col3:
                            st.markdown(f"<span class='gray-text'>(Available: ${lease_cash:,.2f})</span>", unsafe_allow_html=True)

                        if apply_lease_cash:
                            lease_cash_to_use = st.number_input(
                                "Lease Cash Amount",
                                value=lease_cash,
                                key=f"lease_cash_{term_months}",
                                min_value=0.0,
                                max_value=lease_cash
                            )
                        else:
                            lease_cash_to_use = 0.0

                        rebates_to_use = rebates if apply_rebates else 0.0
                        total_ccr = cash_down + rebates_to_use + lease_cash_to_use
                        mf_to_use_adjusted = mf_to_use + st.session_state.settings["money_factor_markup"]

                        payment_calc = calculate_base_and_monthly_payment(
                            S=msrp,
                            RES=residual_value,
                            W=term_months,
                            F=mf_to_use_adjusted,
                            M=962.50,
                            Q=0,
                            B=total_ccr,
                            K=0,
                            U=0,
                            tau=tax_rate
                        )

                        if st.session_state.settings["enable_debug"]:
                            st.write(f"**Money Factor (adjusted):** {mf_to_use_adjusted:.5f}")
                            st.write(f"**Residual Percentage:** {residual_percent:.0%}")
                            st.write(f"**Monthly Payment:** ${payment_calc['Monthly Payment']:,.2f}")
                            st.write(f"**Total Advance (TA):** ${payment_calc['Total Advance']:,.2f}")
                            st.write(f"**Base Payment:** ${payment_calc['Base Payment']:,.2f}")
                            st.write(f"**Residual Value:** ${residual_value:,.2f}")
                        else:
                            st.write(f"**Money Factor (adjusted):** {mf_to_use_adjusted:.5f}")
                            st.write(f"**Residual Percentage:** {residual_percent:.0%}")
                            st.write(f"**Monthly Payment:** ${payment_calc['Monthly Payment']:,.2f}")

    if st.button("Settings"):
        st.session_state.page = "settings"

elif st.session_state.page == "settings":
    st.subheader("Settings")

    # Temporary variables for settings
    temp_settings = st.session_state.settings.copy()

    counties = county_rates[county_column].tolist()
    temp_settings["default_county"] = st.selectbox(
        "Default Tax County",
        counties,
        index=counties.index(st.session_state.settings["default_county"]) if st.session_state.settings["default_county"] in counties else 0
    )

    tiers = ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"]
    temp_settings["default_tier"] = st.selectbox(
        "Default Tier",
        tiers,
        index=tiers.index(st.session_state.settings["default_tier"])
    )

    temp_settings["default_apply_rebates"] = st.checkbox(
        "Default Apply Rebates",
        value=st.session_state.settings["default_apply_rebates"]
    )

    temp_settings["auto_apply_lease_cash"] = st.checkbox(
        "Auto-apply Lease Cash",
        value=st.session_state.settings["auto_apply_lease_cash"]
    )

    temp_settings["money_factor_markup"] = st.number_input(
        "Money Factor Markup",
        min_value=0.0,
        value=st.session_state.settings["money_factor_markup"],
        step=0.0001
    )

    temp_settings["enable_debug"] = st.checkbox(
        "Enable Debug Display",
        value=st.session_state.settings["enable_debug"]
    )

    # Save and Return button
    if st.button("Save and Return"):
        st.session_state.settings = temp_settings
        st.session_state.page = "main"
