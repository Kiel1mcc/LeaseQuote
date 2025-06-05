import streamlit as st
import pandas as pd

# Load lease and locator data
lease_data = pd.read_csv("All_Lease_Programs_Database.csv")
locator_data = pd.read_excel("Locator_Detail_20250605.xlsx")


def is_ev_phev(row: pd.Series) -> bool:
    """Return True if the vehicle qualifies for EV/PHEV incentives."""
    desc = " ".join(
        str(row.get(col, "")) for col in ["Model", "Trim", "ModelDescription"]
    ).lower()
    keywords = ["electric", "plug", "phev", "fuel cell"]
    return any(k in desc for k in keywords)


def main():
    st.title("Lease Quote Calculator")

    vin = st.text_input("Enter VIN:").strip().lower()
    tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
    county_tax = st.number_input("County Tax Rate (%)", value=7.25) / 100
    money_down = st.number_input("Money Down ($)", value=0.0)

    if vin and tier:
        try:
            all_payments = []

            if tier not in lease_data.columns:
                st.error(f"Tier column '{tier}' not found.")
                return

            msrp_row = locator_data[locator_data["VIN"] == vin]
            if msrp_row.empty:
                st.error("VIN not found in locator file.")
                return

            model_number = msrp_row["ModelNumber"].iloc[0]
            st.info(f"🔍 Looking up Model Number: {model_number}")

            if model_number not in lease_data["ModelNumber"].values:
                st.error(f"No lease entries found for model number {model_number}")
                return

            msrp = float(msrp_row["MSRP"].iloc[0])
            st.info(f"✔ VIN matched: Model {model_number}, MSRP ${msrp:,.2f}")

            matches = lease_data[lease_data["ModelNumber"] == model_number]
            matches = matches[~matches[tier].isnull()]
            if matches.empty:
                st.warning("No lease matches found for this tier.")
                return

            available_terms = sorted(matches["Term"].dropna().unique(), key=lambda x: int(x))

            for term in available_terms:
                st.subheader(f"{int(term)}-Month Term")

                options = matches[matches["Term"] == term].copy()
                options["Residual"] = options["Residual"].astype(float)
                best = options.iloc[0]

                try:
                    lease_cash = float(best["LeaseCash"]) if best["LeaseCash"] else 0.0
                except:
                    lease_cash = 0.0

                try:
                    base_mf = float(best[tier])
                    base_residual_pct = float(best["Residual"]) * 100
                except:
                    st.error("Invalid MF or residual data.")
                    return

                st.info(f"➡ Term {term}: MF {base_mf:.5f}, Residual {base_residual_pct:.1f}%")

                term_months = int(term)
                ev_phev = is_ev_phev(best)

                col1, col2, col3 = st.columns([1, 2, 2])
                with col1:
                    single_pay = st.toggle("Single Pay (EV/PHEV)", False, key=f"sp_{term}", disabled=not ev_phev)
                with col2:
                    include_markup = st.toggle("Remove Markup", False, key=f"markup_{term}")
                with col3:
                    include_lease_cash = st.toggle(f"Include Lease Cash (${lease_cash:,.0f})", False, key=f"rebate_{term}")

                toggle_color = '#ff4d4d' if include_markup else '#cccccc'
                st.markdown(
                    f"<style>div[data-testid='stToggle'][key='markup_{term}'] > div:first-child "
                    f"{{ background-color: {toggle_color} !important; }}</style>", unsafe_allow_html=True)

                mf = (base_mf - 0.00015 if single_pay and ev_phev else base_mf) + (0 if include_markup else 0.0004)
                rebate = lease_cash if include_lease_cash else 0.0

                mileage_cols = st.columns(3)
                mile_data = []
                for mileage in ["10K", "12K", "15K"]:
                    if mileage == "10K" and not (33 <= term_months <= 48):
                        mile_data.append((mileage, None, True, base_residual_pct + 1))
                        continue

                    residual_pct = base_residual_pct
                    if mileage == "10K": residual_pct += 1
                    elif mileage == "15K": residual_pct -= 2

                    residual = msrp * (residual_pct / 100)
                    cap_cost = msrp - rebate - money_down
                    rent = (cap_cost + residual) * mf * term_months
                    depreciation = cap_cost - residual
                    base_monthly = (depreciation + rent) / term_months
                    tax = base_monthly * county_tax
                    total_monthly = base_monthly + tax

                    mile_data.append((mileage, total_monthly, False, residual_pct))

                min_payment = min([amt for _, amt, _, _ in mile_data if amt is not None])
                all_payments.extend([amt for _, amt, _, _ in mile_data if amt is not None])

                for i, (mileage, total_monthly, not_available, residual_pct) in enumerate(mile_data):
                    with mileage_cols[i]:
                        if not_available:
                            st.markdown(f"<div style='opacity:0.5'><h4>{mileage} Not Available</h4></div>", unsafe_allow_html=True)
                            continue

                        highlight = "color:#2e86de;"
                        if total_monthly == min_payment:
                            highlight = "font-weight:bold; color:#27ae60;"

                        st.markdown(f"<h4 style='{highlight}'>${total_monthly:.2f} / month</h4>", unsafe_allow_html=True)
                        st.markdown(
                            f"<div style='color:gray; font-size:0.85em;'>MF: {mf:.5f} | Residual: {residual_pct:.1f}%</div>",
                            unsafe_allow_html=True
                        )

        except Exception as e:
            st.error(f"Something went wrong: {e}")
    else:
        st.info("Please enter a VIN and select a tier to begin.")


if __name__ == "__main__":
    main()
