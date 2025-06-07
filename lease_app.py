import streamlit as st
import pandas as pd

# Load lease and locator data
lease_data = pd.read_csv("All_Lease_Programs_Database.csv")
locator_data = pd.read_excel("Locator_Detail_20250605.xlsx")
locator_data.columns = locator_data.columns.str.strip()
locator_data["Vin"] = locator_data["VIN"].astype(str).str.strip().str.lower()

# Load county tax rates
county_df = pd.read_csv("County_Tax_Rates.csv")
county_df["Dropdown_Label"] = county_df["County"] + " (" + county_df["Tax Rate"].astype(str) + "%)"

def is_ev_phev(row: pd.Series) -> bool:
    desc = " ".join(str(row.get(col, "")) for col in ["Model", "Trim", "ModelDescription"]).lower()
    return any(k in desc for k in ["electric", "plug", "phev", "fuel cell"])

def main():
    st.title("Lease Quote Calculator")

    vin = st.text_input("Enter VIN:").strip().lower()
    tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])

    # County dropdown
    selected_county = st.selectbox("Select County:", county_df["Dropdown_Label"])
    county_tax = county_df[county_df["Dropdown_Label"] == selected_county]["Tax Rate"].values[0] / 100

    money_down = st.number_input("Money Down ($)", value=0.0)

    if vin and tier:
        try:
            if tier not in lease_data.columns:
                st.error(f"Tier column '{tier}' not found.")
                return

            msrp_row = locator_data[locator_data["Vin"] == vin]
            if msrp_row.empty:
                st.error("VIN not found in locator file.")
                return

            model_number = msrp_row["ModelNumber"].iloc[0]
            if model_number not in lease_data["ModelNumber"].values:
                st.error("No lease entries found for this vehicle.")
                return

            msrp = float(msrp_row["MSRP"].iloc[0])
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
                    lease_cash = float(best["LeaseCash"])
                except:
                    lease_cash = 0.0

                try:
                    base_mf = float(best[tier])
                    base_residual_pct = float(best["Residual"])
                except Exception as e:
                    st.error(f"Invalid MF or residual data: {e}")
                    return

                term_months = int(term)
                ev_phev = is_ev_phev(best)

                col1, col2, col3 = st.columns([1, 2, 2])
                with col1:
                    single_pay = st.toggle("Single Pay (EV/PHEV)", False, key=f"sp_{term}", disabled=not ev_phev)
                with col2:
                    remove_markup = st.toggle("Remove Markup", False, key=f"markup_{term}")
                with col3:
                    include_lease_cash = st.toggle(f"Apply Lease Cash (${lease_cash:,.0f})", False, key=f"rebate_{term}")

                toggle_color = '#ff4d4d' if remove_markup else '#cccccc'
                st.markdown(f"""
                <style>
                    div[data-testid='stToggle'][key='markup_{term}'] > div:first-child {{
                        background-color: {toggle_color} !important;
                    }}
                </style>
                """, unsafe_allow_html=True)

                # Final MF based on toggles
                mf = (base_mf - 0.00015 if single_pay and ev_phev else base_mf)
                mf += 0 if remove_markup else 0.0004

                # Fees
                doc_fee = 250.00
                acq_fee = 650.00
                title_fee = 15.00
                license_fee = 47.50
                fees_total = doc_fee + acq_fee + title_fee + license_fee

                # Cap cost calc based on lease cash toggle
                cap_cost = msrp + fees_total
                if include_lease_cash:
                    cap_cost -= lease_cash

                # Taxes
                doc_tax = round(doc_fee * county_tax, 2)
                acq_tax = round(acq_fee * county_tax, 2)
                rebate_tax = round(lease_cash * county_tax, 2) if include_lease_cash else 0
                cap_reduction_tax = round(money_down * county_tax, 2)
                total_upfront_tax = doc_tax + acq_tax + rebate_tax + cap_reduction_tax

                mileage_cols = st.columns(3)
                for i, mileage in enumerate(["10K", "12K", "15K"]):
                    if mileage == "10K" and not (33 <= term_months <= 48):
                        with mileage_cols[i]:
                            st.markdown(f"<div style='opacity:0.5'><h4>{mileage} Not Available</h4></div>", unsafe_allow_html=True)
                        continue

                    residual_pct = base_residual_pct * 100
                    if mileage == "10K":
                        residual_pct += 1
                    elif mileage == "15K":
                        residual_pct -= 2

                    residual_value = round(msrp * (residual_pct / 100), 2)
                    depreciation = round(cap_cost - residual_value, 2)
                    rent = round((cap_cost + residual_value) * mf * term_months, 2)
                    base_monthly = round((depreciation + rent) / term_months, 2)
                    monthly_tax = round(base_monthly * county_tax, 2)
                    prorated_upfront_tax = round(total_upfront_tax / term_months, 2)
                    final_monthly = round(base_monthly + monthly_tax + prorated_upfront_tax + 2, 2)

                    with mileage_cols[i]:
                        st.markdown(f"<h4 style='color:#2e86de;'>${final_monthly:.2f} / month</h4>", unsafe_allow_html=True)
                        st.caption(f"MF: {mf:.5f}, Residual: {residual_pct:.1f}%, Fees Taxed: ${total_upfront_tax:.2f}")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
    else:
        st.info("Please enter a VIN and select a tier to begin.")

if __name__ == "__main__":
    main()
