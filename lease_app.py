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
vin_input = vin_input.strip().upper()
tier = st.selectbox("Select Tier:", ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"])

# Load data once and cache for performance
@st.cache_data
def load_reference_data():
    lease_df = pd.read_csv("All_Lease_Programs_Database.csv")
    inventory_df = pd.read_excel("Locator_Detail_Updated.xlsx")
    county_df = pd.read_csv("County_Tax_Rates.csv")
    lease_df["VIN"] = lease_df["VIN"].astype(str).str.strip().str.upper()
    inventory_df["VIN"] = inventory_df["VIN"].astype(str).str.strip().str.upper()
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
def get_vehicle_programs(vin: str, county: str):
    """Return selling price, tax rate and all lease program rows for the VIN."""
    inv_row = inventory_df[inventory_df["VIN"] == vin]
    lease_rows = lease_df[lease_df["VIN"] == vin]
    if inv_row.empty or lease_rows.empty:
        return None

    inv_row = inv_row.iloc[0]
    selling_price = float(inv_row["MSRP"])  # default selling price uses MSRP
    tax_rate = float(county_df[county_df["County"] == county]["Tax Rate"].iloc[0])

    return selling_price, tax_rate, lease_rows


def calculate_quote(
    sp: float,
    residual_pct: float,
    money_factor: float,
    term: int,
    lease_cash: float,
    tax_rate: float,
    trade_value: float,
    cash_down: float,
    settings: dict,
    apply_markup: bool,
):
    """Calculate monthly payment using existing helper functions."""

    K = 0.0
    M = 900.0
    Q = 62.5
    F = money_factor
    if apply_markup:
        F += 0.0004
    F += settings.get("money_factor_markup", 0.0)
    RES = sp * residual_pct
    τ = tax_rate
    W = term

    # Step 1: Initial TopVal calculation with no funds applied
    _, _, debug_pre = calculate_ccr_full(
        SP=sp,
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
        adjust_negative=False,
    )
    initial_topval = debug_pre.get("Initial TopVal", 0.0)
    deal_charges = max(0.0, -initial_topval)

    # Step 2: Prioritize trade value to cover deal charges
    TV_hold = trade_value
    B_hold = cash_down

    TV_applied = min(deal_charges, TV_hold)
    remaining_charges = deal_charges - TV_applied

    B_applied = min(remaining_charges, B_hold)

    TV_final = TV_hold - TV_applied
    B_final = B_hold - B_applied

    adjusted_B = B_applied + TV_applied

    _, monthly_payment, debug_post = calculate_base_and_monthly_payment(
        SP=sp,
        B=B_final,
        rebates=lease_cash,
        TV=TV_final,
        K=K,
        M=M,
        Q=Q,
        RES=RES,
        F=F,
        W=W,
        τ=τ,
    )

    return {
        "deal_charges": deal_charges,
        "adjusted_B": adjusted_B,
        "monthly_payment": monthly_payment,
        "debug": debug_post,
    }

if vin_input:
    programs = get_vehicle_programs(vin_input, county)
    if programs is None:
        st.error("VIN not found in program or inventory data")
    else:
        selling_price_default, tax_rate, lease_rows = programs

        # Allow user to adjust sale price and trade value
        sale_price_input = st.number_input(
            "Sale Price ($)", value=float(selling_price_default), format="%.2f"
        )

        # Iterate through each available lease program
        for _, row in lease_rows.iterrows():
            term = int(row["Term"])
            money_factor = float(row[tier])
            residual_pct = float(row["Residual"])
            lease_cash = float(row.get("LeaseCash", 0.0))

            result = calculate_quote(
                sp=sale_price_input,
                residual_pct=residual_pct,
                money_factor=money_factor,
                term=term,
                lease_cash=lease_cash,
                tax_rate=tax_rate,
                trade_value=trade_value_input,
                cash_down=money_down_slider,
                settings=settings,
                apply_markup=apply_markup,
            )

            with st.expander(f"{term}-Month Program"):
                st.markdown(
                    f"**💵 Monthly Payment: ${result['monthly_payment']:,.2f}**"
                )
                st.markdown(
                    f"_Base: {result['debug'].get('Base Payment', 0.0):.2f}, "
                    f"Tax: {result['debug'].get('Tax Amount', 0.0):.2f}, "
                    f"CCR: {result['debug'].get('CCR', 0.0):.2f}_"
                )
                st.markdown(
                    f"Deal Charges: ${result['deal_charges']:,.2f}, "
                    f"Adjusted B: ${result['adjusted_B']:,.2f}"
                )





        
