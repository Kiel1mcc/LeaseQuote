import streamlit as st
import pandas as pd
import os
import re

# Load lease and locator data
try:
    lease_data = pd.read_csv("All_Lease_Programs_Database.csv")
    lease_data.columns = lease_data.columns.str.strip()
except FileNotFoundError:
    st.error("Lease data file 'All_Lease_Programs_Database.csv' not found.")
    st.stop()

# Determine model column safely
model_column = None
if "MODEL" in lease_data.columns:
    model_column = "MODEL"
elif "ModelNumber" in lease_data.columns:
    model_column = "ModelNumber"
elif "MODEL #" in lease_data.columns:
    model_column = "MODEL #"
elif "MODEL NUMBER" in lease_data.columns:
    model_column = "MODEL NUMBER"
else:
    st.error("No valid model column (MODEL, ModelNumber, MODEL #, MODEL NUMBER) found in lease data.")
    st.stop()

# Debug: Log lease_data columns
st.write(f"Debug - Columns in lease_data: {lease_data.columns.tolist()}")

# Ensure model column is uppercase and clean
lease_data[model_column] = (lease_data[model_column].astype(str)
                           .str.strip()
                           .str.upper()
                           .apply(lambda x: re.sub(r'[^\x20-\x7E]', '', x)))  # Remove non-printable characters

# Load locator data with file validation
excel_file = "Locator_Detail_20250605.xlsx"
if not os.path.exists(excel_file):
    st.error(f"Locator data file '{excel_file}' not found.")
    st.stop()

try:
    locator_data = pd.read_excel(excel_file)
    locator_data.columns = locator_data.columns.str.strip()
    # Normalize VINs to uppercase and remove hidden characters
    locator_data["Vin"] = (locator_data["VIN"].astype(str)
                         .str.strip()
                         .str.upper()
                         .str.replace("\u200b", "")
                         .str.replace("\ufeff", ""))
except Exception as e:
    st.error(f"Failed to load locator data: {e}")
    st.stop()

# Load county tax rates and build Dropdown_Label column
try:
    county_df = pd.read_csv("County_Tax_Rates.csv")
    county_df["Dropdown_Label"] = county_df["County"] + " (" + county_df["Tax Rate"].astype(str) + "% )"
except FileNotFoundError:
    st.error("County tax rates file 'County_Tax_Rates.csv' not found.")
    st.stop()

def is_ev_phev(row: pd.Series) -> bool:
    desc = " ".join(str(row.get(col, "")) for col in ["Model", "Trim", "ModelDescription"]).lower()
    return any(k in desc for k in ["electric", "plug", "phev", "fuel cell"])

def main():
    st.title("Lease Quote Calculator")

    # Normalize input VIN to uppercase and remove hidden characters
    vin = (st.text_input("Enter VIN:", help="VIN will be converted to uppercase for matching")
           .strip()
           .upper()
           .replace("\u200b", "")
           .replace("\ufeff", ""))
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
            # Debug: Log input and data for troubleshooting
            st.write(f"Debug - Input VIN (normalized to uppercase): {vin}")
            st.write(f"Debug - First 5 VINs in locator_data: {locator_data['Vin'].head().tolist()}")
            st.write(f"Debug - Columns in locator_data: {locator_data.columns.tolist()}")

            # Exact VIN match
            msrp_row = locator_data[locator_data["Vin"] == vin]
            if msrp_row.empty:
                st.error(f"VIN '{vin}' not found in locator file. Please check the VIN and try again.")
                return

            # Normalize ModelNumber
            model_number = (msrp_row["ModelNumber"].iloc[0]
                           .strip()
                           .upper()
                           .replace("\u200b", "")
                           .replace("\ufeff", ""))
            model_number = re.sub(r'[^\x20-\x7E]', '', model_number)  # Remove non-printable characters

            # Debug: Log model number and lease data models
            st.write(f"Debug - Model Number from locator_data: {model_number}")
            st.write(f"Debug - Unique Model Numbers in lease_data[{model_column}]: {sorted(lease_data[model_column].unique().tolist())}")

            if model_number not in lease_data[model_column].values:
                st.error(f"No lease entries found for Model Number '{model_number}'.")
                return

            msrp = float(msrp_row["MSRP"].iloc[0])
            matches = lease_data[lease_data[model_column] == model_number]
            matches = matches[~matches[tier].isnull()]
            if matches.empty:
                st.warning("No lease matches found for this tier.")
                return

            # Debug: Log matches to inspect Term values
            st.write(f"Debug - Matching rows for {model_number}: {matches[['ModelNumber', 'Term', tier, 'Residual']].to_dict()}")

            # Validate Term column
            if "Term" not in matches.columns:
                st.error("Term column not found in lease data for this model.")
                return

            # Ensure Term values are numeric and non-null
            matches = matches[matches["Term"].notnull()]
            try:
                available_terms = sorted(matches["Term"].astype(float).unique(), key=lambda x: int(x))
            except ValueError as e:
                st.error(f"Invalid Term values in lease data: {e}")
                return

            if not available_terms:
                st.error("No valid lease terms found for this model.")
                return

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

                    # Compute total_tax_over_term
                    depreciation = (adj_cap_cost - residual_value) / term_months
                    rent_charge = (adj_cap_cost + residual_value) * mf_with_markup
                    base_monthly_payment = depreciation + rent_charge
                    monthly_sales_tax = round(base_monthly_payment * county_tax, 2)
                    total_tax_over_term = monthly_sales_tax * term_months

                    # Calculate final payment
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
