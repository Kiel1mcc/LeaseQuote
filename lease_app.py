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
    selected_county = st.selectbox(
        "Select County:",
        county_df["Dropdown_Label"],
        index=next(iter(county_df[county_df["Dropdown_Label"].str.contains("^Marion", regex=True)].index), 0)
    )

    county_tax = county_df[county_df["Dropdown_Label"] == selected_county]["Tax Rate"].values[0] / 100

    money_down = st.number_input("Money Down ($)", value=0.0)

    # Program settings — allows matching CDK behavior
    program_cap_reduction_percent = 1.0  # Adjust per program if needed

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
                mf = base_mf + 0.0004
                if remove_markup:
                    mf = base_mf
                if single_pay and ev_phev:
                    mf -= 0.00015

                # Fees
                doc_fee = 250.00
                acq_fee = 650.00
                title_fee = 15.00
                license_fee = 47.50
                fees_total = doc_fee + acq_fee + title_fee + license_fee

                # Taxes
                doc_tax = round(doc_fee * county_tax, 2)
                acq_tax = round(acq_fee * county_tax, 2)
                rebate_applied_to_cap_cost = lease_cash * program_cap_reduction_percent
                rebate_tax = round(rebate_applied_to_cap_cost * county_tax, 2)

                cap_reduction_base = money_down + rebate_applied_to_cap_cost
                cap_reduction_tax = round(cap_reduction_base * county_tax, 2)

                # Cap Reduction handling
                cap_reduction_tax_paid = min(money_down, cap_reduction_tax)
                remaining_money_down = max(0, money_down - cap_reduction_tax_paid)

                # Cap Cost Calculation per your CDK flow:
                # Cap Cost Base = MSRP - "Discount" → for now using MSRP as base, assume no manual discount.
                cap_cost_base = msrp
                cap_cost_total = cap_cost_base + fees_total + doc_tax + acq_tax + rebate_tax + title_fee + license_fee

                # Net Cap Cost after Cap Reduction:
                net_cap_cost = cap_cost_total - (remaining_money_down + rebate_applied_to_cap_cost)

                # Residual value:
                residual_value = round(msrp * (base_residual_pct / 100), 2)

                # CDK Section 3 style calculation:
                avg_monthly_dep = round((net_cap_cost - residual_value) / term_months, 2)
                avg_monthly_rent = round(((net_cap_cost + residual_value) * mf) / term_months, 2)
                base_monthly_payment = round(avg_monthly_dep + avg_monthly_rent, 2)

                # Monthly Sales Tax → tax only Depreciation portion:
                monthly_sales_tax = round(avg_monthly_dep * county_tax, 2)

                # Final Monthly Payment:
                final_monthly_payment = base_monthly_payment + monthly_sales_tax

                # Display results exactly like CDK Section 3:
                st.markdown(f"""
                <h4 style='color:#2e86de;'>Lease Payment Breakdown</h4>
                <ul>
                    <li><b>Depreciation (D):</b> ${avg_monthly_dep:.2f}</li>
                    <li><b>Rent Charge (E):</b> ${avg_monthly_rent:.2f}</li>
                    <li><b>Base Monthly Payment (F):</b> ${base_monthly_payment:.2f}</li>
                    <li><b>Monthly Sales Tax:</b> ${monthly_sales_tax:.2f}</li>
                    <li><b>Total Monthly Payment:</b> ${final_monthly_payment:.2f}</li>
                </ul>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Something went wrong: {e}")
    else:
        st.info("Please enter a VIN and select a tier to begin.")

if __name__ == "__main__":
    main()
