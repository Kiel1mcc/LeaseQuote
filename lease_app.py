import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("All_Lease_Programs_Database.csv")

df = load_data()

# UI
st.title("Lease Calculator")

vin = st.text_input("Enter VIN").strip().upper()
tier = st.selectbox("Select Credit Tier", ["Tier 1", "Tier 5", "Tier 6", "Tier 7", "Tier 8"])
county_tax = st.number_input("County Tax Rate (%)", value=7.25, step=0.01)
money_down = st.number_input("Money Down ($)", value=0.0, step=100.0)

if vin:
    matches = df[(df["VIN"].str.upper() == vin) & (df["TIER"] == tier)]
    if matches.empty:
        st.warning("No matching lease options found.")
    else:
        st.subheader("Estimated Payments:")
        for term in sorted(matches["TERM"].unique(), key=lambda x: int(x)):
            options = matches[matches["TERM"] == term]
            best = options.loc[options["LEASE CASH"].astype(float).idxmax()]

            try:
                msrp = float(best["MSRP"])
                lease_cash = float(best["LEASE CASH"])
                mf = float(best["MONEY FACTOR"])
                residual_pct = float(best["RESIDUAL"])
                term_months = int(best["TERM"])

                residual = msrp * (residual_pct / 100)
                cap_cost = msrp - lease_cash - money_down
                rent = (cap_cost + residual) * mf * term_months
                depreciation = cap_cost - residual
                base_monthly = (depreciation + rent) / term_months
                tax = base_monthly * (county_tax / 100)
                total_monthly = base_monthly + tax

                st.markdown(f"**{term} months:** ${total_monthly:.2f}/mo (Residual: {residual_pct}%)")

            except:
                st.write(f"{term} months: Invalid data")

