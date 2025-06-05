import streamlit as st
import pandas as pd

# Load lease program data
@st.cache_data
def load_data():
    return pd.read_csv("All_Lease_Programs_Database.csv")

data = load_data()

st.title("Lease Quote Calculator")

vin = st.text_input("Enter VIN:").strip().lower()
tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
county_tax = st.number_input("County Tax Rate (%)", value=7.25) / 100
money_down = st.number_input("Money Down ($)", value=0.0)

if vin and tier:
    matches = data[(data["VIN"].str.lower() == vin) & (data["TIER"] == tier)]

    if matches.empty:
        st.warning("No matching lease options found.")
    else:
        available_terms = sorted(matches["TERM"].dropna().unique(), key=lambda x: int(x))

        for term in available_terms:
            st.subheader(f"{term}-Month Term")

            options = matches[matches["TERM"] == term]
            best = options.loc[options["LEASE CASH"].astype(float).idxmax()]

            msrp = float(best["MSRP"])
            lease_cash = float(best["LEASE CASH"]) if best["LEASE CASH"] else 0.0
            base_mf = float(best["MONEY FACTOR"])
            base_residual_pct = float(best["RESIDUAL"])
            term_months = int(term)

            col1, col2, col3 = st.columns([1, 2, 2])
            with col2:
                include_markup = st.toggle("Include Markup", value=True, key=f"markup_{term}")
            with col3:
                include_lease_cash = st.toggle(f"Include Lease Cash (${lease_cash:,.0f})", value=False, key=f"rebate_{term}")

            mf = base_mf if include_markup else base_mf - 0.0004
            rebate = lease_cash if include_lease_cash else 0.0

            mileage_cols = st.columns(3)
            for i, mileage in enumerate(["10K", "12K", "15K"]):
                with mileage_cols[i]:
                    if mileage == "10K" and not (33 <= term_months <= 48):
                        st.markdown(f"<div style='opacity:0.5'><h4>{mileage} Not Available</h4></div>", unsafe_allow_html=True)
                        continue

                    residual_pct = base_residual_pct
                    if mileage == "10K" and 33 <= term_months <= 48:
                        residual_pct += 1
                    elif mileage == "15K":
                        residual_pct -= 2

                    residual = msrp * (residual_pct / 100)
                    cap_cost = msrp - rebate - money_down
                    rent = (cap_cost + residual) * mf * term_months
                    depreciation = cap_cost - residual
                    base_monthly = (depreciation + rent) / term_months
                    tax = base_monthly * county_tax
                    total_monthly = base_monthly + tax

                    st.markdown(f"<h4 style='color:#2e86de;'>${total_monthly:.2f} / month</h4>", unsafe_allow_html=True)
                    st.caption(f"Mileage: {mileage}, Residual: {residual_pct}%, MF: {mf:.5f}, Cap Cost: ${cap_cost:.2f}")
else:
    st.info("Please enter a VIN and select a tier to begin.")
