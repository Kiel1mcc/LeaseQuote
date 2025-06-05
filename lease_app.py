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
        terms = sorted(matches["TERM"].dropna().unique(), key=lambda x: int(x))

        for term in terms:
            st.subheader(f"{term}-Month Term")

            term_rows = matches[matches["TERM"] == term]
            if term_rows.empty:
                continue

            base_row = term_rows.iloc[0]
            msrp = float(base_row["MSRP"])
            lease_cash = float(base_row["LEASE CASH"])
            base_mf = float(base_row["MONEY FACTOR"])
            base_residual = float(base_row["RESIDUAL"])

            apply_markup_all = st.checkbox(f"Apply Markup to All {term}-Month Options", key=f"markup_all_{term}")
            apply_rebate_all = st.checkbox(f"Apply Lease Cash to All {term}-Month Options", key=f"rebate_all_{term}")

            st.markdown("| Mileage | Residual % | Monthly Payment | Markup | Lease Cash |")
            st.markdown("|---------|-------------|------------------|--------|-------------|")

            for mileage in ["10K", "12K", "15K"]:
                if mileage == "10K" and 33 <= int(term) <= 48:
                    residual = base_residual + 1
                elif mileage == "15K":
                    residual = base_residual - 2
                else:
                    residual = base_residual

                row_key = f"{term}_{mileage}"
                include_markup = st.checkbox("", value=apply_markup_all, key=f"markup_{row_key}")
                include_rebate = st.checkbox("", value=apply_rebate_all, key=f"rebate_{row_key}")

                mf = base_mf + 0.0004 if include_markup else base_mf
                rebate = lease_cash if include_rebate else 0
                cap_cost = msrp - rebate - money_down
                residual_value = msrp * (residual / 100)
                rent_charge = (cap_cost + residual_value) * mf * int(term)
                depreciation = cap_cost - residual_value
                base_monthly = (depreciation + rent_charge) / int(term)
                tax = base_monthly * county_tax
                total_monthly = base_monthly + tax

                st.markdown(f"| {mileage} | {residual:.1f}% | **${total_monthly:.2f}** | {'✅' if include_markup else '❌'} | {'✅' if include_rebate else '❌'} |")
else:
    st.info("Please enter a VIN and select a tier to begin.")
