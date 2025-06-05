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
    all_payments = []
    matches = data[(data["VIN"].str.lower() == vin) & (data["TIER"] == tier)]

    if matches.empty:
        st.warning("No matching lease options found.")
    else:
        available_terms = sorted(matches["TERM"].dropna().unique(), key=lambda x: int(x))

        for term in available_terms:
            st.subheader(f"{int(term)}-Month Term")

            options = matches[matches["TERM"] == term]
            best = options.loc[options["RESIDUAL"].astype(float).idxmax()]

            msrp = float(best["MSRP"])
            lease_cash = float(best["LEASE CASH"]) if best["LEASE CASH"] else 0.0
            base_mf = float(best["MONEY FACTOR"])
            base_residual_pct = float(best["RESIDUAL"])
            term_months = int(term)

            col1, col2, col3 = st.columns([1, 2, 2])
            with col2:
                include_markup = st.toggle("Remove Markup", value=False, key=f"markup_{term}")
            toggle_color = '#ff4d4d' if include_markup else '#cccccc'
            st.markdown(f"""
                <style>
                    div[data-testid='stToggle'][key='markup_{term}'] > div:first-child {{
                        background-color: {toggle_color} !important;
                    }}
                </style>
            """, unsafe_allow_html=True)
            with col3:
                include_lease_cash = st.toggle(f"Include Lease Cash (${lease_cash:,.0f})", value=False, key=f"rebate_{term}")

            mf = base_mf + 0.0004 if not include_markup else base_mf
            rebate = lease_cash if include_lease_cash else 0.0

            mileage_cols = st.columns(3)
            mile_data = []
            for i, mileage in enumerate(["10K", "12K", "15K"]):
                if mileage == "10K" and not (33 <= term_months <= 48):
                    mile_data.append((mileage, None, True))
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

                mile_data.append((mileage, total_monthly, False))

            mile_min_payment = min([amt for _, amt, na in mile_data if amt is not None])
            all_payments.extend([amt for _, amt, na in mile_data if amt is not None])
            
            mileage_cols = st.columns(3)
            term_min = min([amt for _, amt, na in mile_data if amt is not None])
            for i, (mileage, total_monthly, not_available) in enumerate(mile_data):
                with mileage_cols[i]:
                    if not_available:
                        st.markdown(f"<div style='opacity:0.5'><h4>{mileage} Not Available</h4></div>", unsafe_allow_html=True)
                        continue

                    if total_monthly == min(all_payments) and total_monthly == mile_min_payment:
                        highlight = "font-weight:bold; color:#27ae60;"  # Green for lowest overall
                    elif total_monthly == mile_min_payment:
                        highlight = "font-weight:bold; color:#f1c40f;"  # Yellow for lowest in term
                    else:
                        highlight = "color:#2e86de;"

                    label = "<span style='font-size:0.8em;'> - Lowest Payment</span>" if total_monthly == min(all_payments) else ""
                    st.markdown(f"<h4 style='{highlight}'>${total_monthly:.2f} / month{label}</h4>", unsafe_allow_html=True)
                    st.caption(f"Mileage: {mileage}, Residual: {residual_pct}%, MF: {mf:.5f}, Cap Cost: ${cap_cost:.2f}")
else:
    st.info("Please enter a VIN and select a tier to begin.")
