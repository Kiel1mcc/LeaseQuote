import streamlit as st
import pandas as pd

# Load lease and locator data
lease_data = pd.read_csv("All_Lease_Programs_Database.csv")
lease_data.columns = lease_data.columns.str.strip().str.upper()

# Determine model column safely
if "MODEL #" in lease_data.columns:
    model_column = "MODEL #"
elif "MODEL NUMBER" in lease_data.columns:
    model_column = "MODEL NUMBER"
elif "MODEL" in lease_data.columns:
    model_column = "MODEL"
else:
    st.error("MODEL column not found in lease data.")
    st.stop()

locator_data = pd.read_excel("Locator_Detail_20250605.xlsx")
locator_data.columns = locator_data.columns.str.strip()
locator_data["Vin"] = locator_data["VIN"].astype(str).str.strip().str.lower()

# Load county tax rates and build Dropdown_Label column
county_df = pd.read_csv("County_Tax_Rates.csv")
county_df["Dropdown_Label"] = county_df["County"] + " (" + county_df["Tax Rate"].astype(str) + "% )"

def is_ev_phev(row: pd.Series) -> bool:
    desc = " ".join(str(row.get(col, "")) for col in ["Model", "Trim", "ModelDescription"]).lower()
    return any(k in desc for k in ["electric", "plug", "phev", "fuel cell"])

def main():
    st.title("Lease Quote Calculator")

    vin = st.text_input("Enter VIN:").strip().lower()
    tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])

    selected_county = st.selectbox(
        "Select County:",
        county_df["Dropdown_Label"],
        index=int(county_df[county_df["Dropdown_Label"].str.startswith("Marion")].index[0])
    )
    county_tax = county_df[county_df["Dropdown_Label"] == selected_county]["Tax Rate"].values[0] / 100

    money_down = st.number_input("Money Down ($)", value=0.0)

    if vin and tier:
        try:
            msrp_row = locator_data[locator_data["Vin"] == vin]
            if msrp_row.empty:
                st.error("VIN not found in locator file.")
                return

            model_number = msrp_row["ModelNumber"].iloc[0].strip().upper()
            if model_number not in lease_data[model_column].values:
                st.error("No lease entries found for this vehicle.")
                return

            msrp = float(msrp_row["MSRP"].iloc[0])
            matches = lease_data[lease_data[model_column] == model_number]
            matches = matches[~matches[tier].isnull()]
            if matches.empty:
                st.warning("No lease matches found for this tier.")
                return

            available_terms = sorted(matches["TERM"].dropna().unique(), key=lambda x: int(x))

            for term in available_terms:
                st.subheader(f"{int(term)}-Month Term")
                options = matches[matches["TERM"] == term].copy()
                options["RESIDUAL"] = options["RESIDUAL"].astype(float)
                best = options.iloc[0]

                try:
                    lease_cash = float(best["LEASE CASH"])
                except:
                    lease_cash = 0.0

                try:
                    base_mf = float(best[tier])
                    base_residual_pct = float(best["RESIDUAL"])
                except Exception as e:
                    st.error(f"Invalid MF or residual data: {e}")
                    return

                term_months = int(term)
                ev_phev = is_ev_phev(best)

                col1, col2, col3 = st.columns([1, 2, 2], gap="small")
                with col1:
                    single_pay = st.toggle("Single Pay (EV/PHEV)", False, key=f"sp_{term}", disabled=not ev_phev)
                with col2:
                    remove_markup = st.toggle("Remove Markup", False, key=f"markup_{term}")
                with col3:
                    include_lease_cash = st.toggle(f"Apply Lease Cash (${lease_cash:,.0f})", False, key=f"rebate_{term}")

                mf = (base_mf - 0.00015 if single_pay and ev_phev else base_mf)
                mf_with_markup = mf + (0 if remove_markup else 0.0004)

                doc_fee = 250.00
                acq_fee = 650.00
                title_fee = 15.00
                license_fee = 47.50
                fees_total = doc_fee + acq_fee + title_fee + license_fee

                cap_cost = msrp + fees_total
                if include_lease_cash:
                    cap_cost -= lease_cash

                adj_cap_cost = cap_cost - money_down

                mileage_cols = st.columns(3, gap="small")
                for i, mileage in enumerate(["10K", "12K", "15K"]):
                    if mileage == "10K" and not (33 <= term_months <= 48):
                        with mileage_cols[i]:
                            st.markdown(f"<div style='opacity:0.5'><h4>{mileage} Not Available</h4></div>", unsafe_allow_html=True)
                        continue

                    residual_pct = base_residual_pct
                    if mileage == "10K":
                        residual_pct += 1
                    elif mileage == "15K":
                        residual_pct -= 2

                    residual_value = msrp * (residual_pct / 100)

                    # This is only to compute total_tax_over_term to match your 27031 logic
                    depreciation = (adj_cap_cost - residual_value) / term_months
                    rent_charge = (adj_cap_cost + residual_value) * mf_with_markup
                    base_monthly_payment = depreciation + rent_charge
                    monthly_sales_tax = round(base_monthly_payment * county_tax, 2)
                    total_tax_over_term = monthly_sales_tax * term_months

                    # Now your flow starts here:
                    cap_cost_plus_tax = adj_cap_cost + total_tax_over_term

                    avg_monthly_depreciation = (cap_cost_plus_tax - residual_value) / term_months
                    avg_monthly_lease_charge = mf_with_markup * (cap_cost_plus_tax + residual_value)
                    payment = avg_monthly_depreciation + avg_monthly_lease_charge

                    with mileage_cols[i]:
                        st.markdown(f"""
                        <h4 style='color:#2e86de;'>${payment:.2f} / month (Your formula)</h4>
                        <p>
                        <b>Avg Monthly Depreciation:</b> ${avg_monthly_depreciation:.2f} <br>
                        <b>Avg Monthly Lease Charge:</b> ${avg_monthly_lease_charge:.2f} <br>
                        <b>Payment (Your formula):</b> ${payment:.2f}
                        </p>
                        """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Something went wrong: {e}")
    else:
        st.info("Please enter a VIN and select a tier to begin.")

if __name__ == "__main__":
    main()
