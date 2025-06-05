import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    return pd.read_csv("All_Lease_Programs_Database.csv")

df = load_data()

st.title("Lease Calculator")

vin = st.text_input("Enter VIN").strip().upper()

tier = st.selectbox("Select Credit Tier", [
    "Tier 1", "Tier 2", "Tier 3", "Tier 4",
    "Tier 5", "Tier 6", "Tier 7", "Tier 8"
])

county_tax = st.number_input("County Tax Rate (%)", value=7.25, step=0.01)
money_down = st.number_input("Money Down ($)", value=0.0, step=100.0)

if vin:
    matches = df[(df["VIN"].str.upper() == vin) & (df["TIER"] == tier)]

    if matches.empty:
        st.warning("No matching lease options found.")
    else:
        st.subheader(f"Payment Options for {tier}")
        for i, term in enumerate(sorted(matches["TERM"].unique(), key=lambda x: int(x))):
            options = matches[matches["TERM"] == term]
            best = options.loc[options["LEASE CASH"].astype(float).idxmax()]

            msrp = float(best["MSRP"])
            lease_cash = float(best["LEASE CASH"]) if best["LEASE CASH"] else 0.0
            base_mf = float(best["MONEY FACTOR"])
            residual_pct = float(best["RESIDUAL"])
            term_months = int(term)

            # Per-term toggles
            st.markdown(f"### {term_months} Month Term")
            col1, col2 = st.columns(2)
            with col1:
                include_markup = st.toggle("Include Markup", value=True, key=f"markup_{term}")
            with col2:
                include_lease_cash = st.toggle("Include Lease Cash", value=True, key=f"leasecash_{term}")

            # Apply toggles
            mf = base_mf if include_markup else base_mf - 0.0004
            rebate = lease_cash if include_lease_cash else 0.0

            # Calculate lease payment
            residual = msrp * (residual_pct / 100)
            cap_cost = msrp - rebate - money_down
            rent = (cap_cost + residual) * mf * term_months
            depreciation = cap_cost - residual
            base_monthly = (depreciation + rent) / term_months
            tax = base_monthly * (county_tax / 10_*_
