import streamlit as st
import pandas as pd

@st.cache_data
def load_lease_data():
    df = pd.read_csv("All_Lease_Programs_Database.csv")
    df.columns = df.columns.str.strip().str.title()
    return df

@st.cache_data
def load_locator_data():
    df = pd.read_excel("Locator_Detail_20250605.xlsx")
    df.columns = df.columns.str.strip().str.title()
    df["Vin"] = df["Vin"].str.upper()
    return df

lease_data = load_lease_data()
locator_data = load_locator_data()

st.title("Lease Quote Calculator")

vin_input = st.text_input("Enter VIN:").strip().upper()
tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
county_tax = st.number_input("County Tax Rate (%)", value=7.25) / 100
money_down = st.number_input("Money Down ($)", value=0.0)

if vin_input and tier:
    all_payments = []

    if tier not in lease_data.columns:
        st.error(f"Tier column '{tier}' not found. Your data columns are: {lease_data.columns.tolist()}")
    else:
        lease_matches = lease_data[lease_data["Vin"].str.upper() == vin_input]
        lease_matches = lease_matches[~lease_matches[tier].isnull()]

        locator_match = locator_data[locator_data["Vin"] == vin_input]

        if lease_matches.empty:
            st.warning("No matching lease options found.")
        elif locator_match.empty:
            st.warning("VIN not found in Locator file. Can't determine MSRP.")
        else:
            msrp_str = str(locator_match.iloc[0]["Msrp"]).replace("$", "").replace(",", "").strip()
            try:
                msrp = float(msrp_str)
            except:
                st.error(f"Could not parse MSRP from locator file: {locator_match.iloc[0]['Msrp']}")
                st.stop()

            available_terms = sorted(lease_matches["Term"].dropna().unique(), key=lambda x: int(x))

            for term in available_terms:
                st.subheader(f"{int(term)}-Month Term")
                term_data = lease_matches[lease_matches["Term"] == term].copy()

                base_mf = float(term_data.iloc[0][tier])
                base_residual_pct = float(term_data.iloc[0]["Residual"]) * 100
                lease_cash = float(term_data.iloc[0].get("Leasecash", 0) or 0)
                term_months = int(term)

                col1, col2, col3 = st.columns([1, 2, 2])
                with col2:
                    include_markup = st.toggle("Remove Markup", value=False, key=f"markup_{term}")
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

                    residual_pct = base_residual_pct + 1 if mileage == "10K" else base_residual_pct - 2 if mileage == "15K" else base_r
