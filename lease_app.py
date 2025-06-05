import streamlit as st
import pandas as pd

# Load lease program data
@st.cache_data
def load_lease_data() -> pd.DataFrame:
    """Return normalized lease program information."""
    df = pd.read_csv("All_Lease_Programs_Database.csv")
    df.columns = df.columns.str.strip().str.title()  # Normalize column names
    return df

# Load locator file for MSRP
@st.cache_data
def load_locator_data() -> pd.DataFrame:
    """Return cleaned locator data with MSRP information."""
    df = pd.read_excel("Locator_Detail_20250605.xlsx", engine="openpyxl")
    df.columns = df.columns.str.strip().str.title()
    df["Vin"] = df["Vin"].str.strip().str.lower()
    df["Msrp"] = df["Msrp"].replace('[\$,]', '', regex=True).astype(float)
    return df

lease_data: pd.DataFrame = load_lease_data()
locator_data: pd.DataFrame = load_locator_data()


def main() -> None:
    """Run the Streamlit lease quote calculator."""

    st.title("Lease Quote Calculator")

    vin = st.text_input("Enter VIN:").strip().lower()
    tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
    county_tax = st.number_input("County Tax Rate (%)", value=7.25) / 100
    money_down = st.number_input("Money Down ($)", value=0.0)

    if vin and tier:
        all_payments = []

        if tier not in lease_data.columns:
            st.error(f"Tier column '{tier}' not found. Your data columns are: {lease_data.columns.tolist()}")
        else:
            matches = lease_data[lease_data["Vin"].str.lower() == vin]
            matches = matches[~matches[tier].isnull()]

            if matches.empty:
                st.warning("No matching lease options found.")
            else:
                msrp_row = locator_data[locator_data["Vin"] == vin]
                if msrp_row.empty:
                    st.error("VIN found in lease database but not in locator file. Please update MSRP source.")
                else:
                    msrp = float(msrp_row["Msrp"].iloc[0])
                    available_terms = sorted(matches["Term"].dropna().unique(), key=lambda x: int(x))

                    for term in available_terms:
                        st.subheader(f"{int(term)}-Month Term")

                        options = matches[matches["Term"] == term].copy()
                        options["Residual"] = options["Residual"].astype(float)
                        best = options.iloc[0]

                        lease_cash = float(best["Leasecash"]) if best["Leasecash"] else 0.0
                        base_mf = float(best[tier])
                        base_residual_pct = float(best["Residual"]) * 100
                        term_months = int(term)

                        col1, col2, col3 = st.columns([1, 2, 2])
                        with col2:
                            include_markup = st.toggle("Remove Markup", value=False, key=f"markup_{term}")
                        toggle_color = '#ff4d4d' if include_markup else '#cccccc'
                        st.markdown(
                            f"""
                            <style>
                                div[data-testid='stToggle'][key='markup_{term}'] > div:first-child {{
                                    background-color: {toggle_color} !important;
                                }}
                            </style>
                            """,
                            unsafe_allow_html=True
                        )
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

                            if mileage == "12K":
                                residual_pct = base_residual_pct
                            elif mileage == "10K":
                                residual_pct = base_residual_pct + 1
                            elif mileage == "15K":
                                residual_pct = base_residual_pct - 2
                            else:
                                residual_pct = None

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
                        for i, (mileage, total_monthly, not_available) in enumerate(mile_data):
                            with mileage_cols[i]:
                                if not_available:
                                    st.markdown(f"<div style='opacity:0.5'><h4>{mileage} Not Available</h4></div>", unsafe_allow_html=True)
                                    continue

                                if total_monthly == min(all_payments) and total_monthly == mile_min_payment:
                                    highlight = "font-weight:bold; color:#27ae60;"  # green
                                elif total_monthly == mile_min_payment:
                                    highlight = "font-weight:bold; color:#f1c40f;"  # yellow
                                else:
                                    highlight = "color:#2e86de;"  # blue

                                label = "<span style='font-size:0.8em;'> - Lowest Payment</span>" if total_monthly == min(all_payments) else ""
                                st.markdown(f"<h4 style='{highlight}'>${total_monthly:.2f} / month{label}</h4>", unsafe_allow_html=True)
                                st.caption(f"Mileage: {mileage}, Residual: {residual_pct}%, MF: {mf:.5f}, Cap Cost: ${cap_cost:.2f}")
    else:
        st.info("Please enter a VIN and select a tier to begin.")


if __name__ == "__main__":
    main()
