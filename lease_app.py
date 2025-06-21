import streamlit as st
import pandas as pd
import numpy as np
from lease_calculations import calculate_base_and_monthly_payment, calculate_ccr_full
from setting_page import show_settings

st.set_page_config(page_title="Lease Quote Calculator", layout="wide")

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Quote Calculator", "Settings"])
if page == "Settings":
    show_settings()
    st.stop()

st.markdown("""
<style>
.toggle-green .stToggleSwitch [data-baseweb="switch"] {
  background-color: #28a745 !important;
}
.toggle-red .stToggleSwitch [data-baseweb="switch"] {
  background-color: #dc3545 !important;
}
</style>
""", unsafe_allow_html=True)

# Inputs
vin_input = st.text_input("Enter VIN:")
tier = st.selectbox("Select Tier:", ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"])

# Load data once and cache for performance
@st.cache_data
def load_reference_data():
    lease_df = pd.read_csv("All_Lease_Programs_Database.csv")
    inventory_df = pd.read_excel("Locator_Detail_Updated.xlsx")
    county_df = pd.read_csv("County_Tax_Rates.csv")
    county_df["Tax Rate"] = county_df["Tax Rate"].astype(float) / 100
    return lease_df, inventory_df, county_df

lease_df, inventory_df, county_df = load_reference_data()

# County list with default pulled from settings
counties = county_df["County"].tolist()
settings = st.session_state.get("settings", {})
default_county = settings.get("default_county", counties[0])
county = st.selectbox("Select County:", counties, index=counties.index(default_county))
trade_value_input = st.number_input("Trade Value ($)", value=0.0)
money_down_slider = st.number_input("Default Down Payment ($)", value=0.0)
apply_markup = st.checkbox("Apply Money Factor Markup (+0.0004)")

# Lookup vehicle data from CSV/Excel references
def get_vehicle_data(vin: str, tier: str, county: str):
    inv_row = inventory_df[inventory_df["VIN"] == vin]
    lease_rows = lease_df[lease_df["VIN"] == vin]
    if inv_row.empty or lease_rows.empty:
        return None

    # Prefer 36 month term if available
    row = lease_rows[lease_rows["Term"] == 36]
    if row.empty:
        row = lease_rows.iloc[[0]]
    row = row.iloc[0]
    inv_row = inv_row.iloc[0]

    selling_price = float(inv_row["MSRP"])  # simple example uses MSRP
    residual_value = selling_price * float(row["Residual"])
    money_factor = float(row[tier])
    term = int(row["Term"])
    tax_rate = float(county_df[county_df["County"] == county]["Tax Rate"].iloc[0])
    lease_cash = float(row.get("LeaseCash", 0))

    return {
        "selling_price": selling_price,
        "residual_value": residual_value,
        "money_factor": money_factor,
        "term": term,
        "tax_rate": tax_rate,
        "lease_cash": lease_cash,
    }

if vin_input:
    vehicle_data = get_vehicle_data(vin_input, tier, county)
    if vehicle_data is None:
        st.error("VIN not found in program or inventory data")
    else:
        selling_price = vehicle_data["selling_price"]
        residual_value = vehicle_data["residual_value"]
        money_factor = vehicle_data["money_factor"]
        term = vehicle_data["term"]
        tax_rate = vehicle_data["tax_rate"]
        lease_cash = vehicle_data.get("lease_cash", 0.0)

        # Fees and other variables
        K = 0.0
        M = 900.0
        Q = 62.5
        F = money_factor
        if apply_markup:
            F += 0.0004
        F += settings.get("money_factor_markup", 0.0)
        W = term
        τ = tax_rate
        SP = selling_price
        RES = residual_value
        U = 0.0

        # Step 1: Initial TopVal calculation with no funds applied
        initial_ccr, _, debug_pre = calculate_ccr_full(
            SP=SP,
            B=0.0,
            rebates=lease_cash,
            TV=0.0,
            K=K,
            M=M,
            Q=Q,
            RES=RES,
            F=F,
            W=W,
            τ=τ,
            adjust_negative=False
        )
        initial_topval = debug_pre.get("Initial TopVal", 0.0)
        deal_charges = max(0.0, -initial_topval)
        st.markdown(f"**🛠️ Deal Charges (Uncovered TopVal): ${deal_charges:,.2f}**")

        # Step 2: Prioritize trade value to cover deal charges
        TV_hold = trade_value_input
        B_hold = money_down_slider

        TV_applied = min(deal_charges, TV_hold)
        remaining_charges = deal_charges - TV_applied

        B_applied = min(remaining_charges, B_hold)

        # What’s left after covering deal charges
        TV_final = TV_hold - TV_applied  # Can reduce SP
        B_final = B_hold - B_applied     # Goes to CCR

        adjusted_B = B_applied + TV_applied

        # Final CCR calculation with true funds
        final_ccr, monthly_payment, debug_post = calculate_base_and_monthly_payment(
            SP=SP,
            B=B_final,
            rebates=lease_cash,
            TV=TV_final,
            K=K,
            M=M,
            Q=Q,
            RES=RES,
            F=F,
            W=W,
            τ=τ
        )

        # Display Output
        st.markdown(f"**📊 Adjusted B (CCR Cash Applied): ${adjusted_B:,.2f}**")
        st.markdown(f"**💵 Monthly Payment: ${monthly_payment:,.2f}**")
        st.markdown(
            f"_Base: {debug_post.get('Base Payment', 0.0):.2f}, "
            f"Tax: {debug_post.get('Tax Amount', 0.0):.2f}, "
            f"CCR: {debug_post.get('CCR', 0.0):.2f}_"
        )

        st.markdown(
            """\
    ## 🔍 How Deal Charges Were Covered:
    - From Trade Value: ${TV_applied:,.2f}
    - From Cash Down: ${B_applied:,.2f}
    """
        )

