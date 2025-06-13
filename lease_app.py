import streamlit as st
import pandas as pd
import re

# Load data files with error handling
try:
    lease_data = pd.read_csv("All_Lease_Programs_Database (3).csv")
    lease_data.columns = lease_data.columns.str.strip()
except FileNotFoundError:
    st.error("Lease data file 'All_Lease_Programs_Database (3).csv' not found.")
    st.stop()

# Determine the model column dynamically
model_column = None
for col in ["ModelNumber", "MODEL", "MODEL #", "MODEL NUMBER"]:
    if col in lease_data.columns:
        model_column = col
        break
if model_column is None:
    st.error("No valid model column found in lease data.")
    st.stop()

# Clean the model column
lease_data[model_column] = (lease_data[model_column].astype(str)
                           .str.strip()
                           .str.upper()
                           .apply(lambda x: re.sub(r'[^\x20-\x7E]', '', x)))

try:
    county_df = pd.read_csv("County_Tax_Rates.csv")
    county_df.columns = county_df.columns.str.strip()
    county_df["Dropdown_Label"] = county_df["County"] + " (" + county_df["Tax Rate"].astype(str) + "%)"
except FileNotFoundError:
    st.error("County tax rates file 'County_Tax_Rates (1).csv' not found.")
    st.stop()

try:
    locator_data = pd.read_excel("Locator_Detail_20250605.xlsx")
    locator_data.columns = locator_data.columns.str.strip()
    locator_data["VIN"] = (locator_data["VIN"].astype(str)
                         .str.strip()
                         .str.upper()
                         .str.replace("\u200b", "")
                         .str.replace("\ufeff", ""))
except FileNotFoundError:
    st.error("Locator data file 'Locator_Detail_20250605.xlsx' not found.")
    st.stop()

# Function to calculate lease details based on user-provided CCR
def calculate_lease_details(ccr, msrp, lease_cash, residual_value, term_months, mf, county_tax, q_value, fixed_fees):
    gross_cap_cost = msrp - lease_cash
    adjusted_cap_cost = gross_cap_cost - ccr
    monthly_depreciation = (adjusted_cap_cost - residual_value) / term_months
    monthly_rent_charge = (adjusted_cap_cost + residual_value) * mf
    base_payment = monthly_depreciation + monthly_rent_charge
    monthly_ltr_fee = q_value / term_months
    monthly_payment_pre_tax = base_payment + monthly_ltr_fee
    monthly_tax = monthly_payment_pre_tax * county_tax
    total_monthly_payment = monthly_payment_pre_tax + monthly_tax
    ccr_tax = ccr * county_tax
    first_payment = total_monthly_payment
    total_das = ccr + ccr_tax + first_payment + fixed_fees
    return {
        "Monthly_Payment": round(total_monthly_payment, 2),
        "Total_DAS": round(total_das, 2)
    }

# Main application function
def main():
    st.title("Lease Quote Calculator")
    
    # User inputs
    vin = st.text_input("Enter VIN:", help="VIN will be converted to uppercase for matching").strip().upper()
    tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
    selected_county = st.selectbox("Select County:", county_df["Dropdown_Label"])
    county_tax = county_df[county_df["Dropdown_Label"] == selected_county]["Tax Rate"].values[0] / 100
    ccr = st.number_input("Capitalized Cost Reduction (CCR) ($)", value=0.0, min_value=0.0, help="Amount paid upfront to reduce the lease cost")
    
    # Explanatory text
    st.markdown("""
    **Calculation Details:**
    - **Capitalized Cost Reduction (CCR):** The amount you pay upfront to reduce the lease cost.
    - **Total Due at Signing (DAS):** Includes CCR, CCR tax, first month's payment, and fixed fees ($962.50).
    - **Monthly Payment:** Includes depreciation, rent charge, monthly fees, and tax.
    """)
    
    if vin and tier:
        try:
            # Match VIN to vehicle details
            msrp_row = locator_data[locator_data["VIN"] == vin]
            if msrp_row.empty:
                st.error(f"VIN '{vin}' not found in locator file.")
                return
            
            model_number = msrp_row["ModelNumber"].iloc[0].strip().upper()
            model_number = re.sub(r'[^\x20-\x7E]', '', model_number)
            msrp = float(msrp_row["MSRP"].iloc[0].replace('$', '').replace(',', ''))
            
            # Display vehicle information
            st.write(f"Vehicle: {msrp_row['Model'].iloc[0]} {msrp_row['Trim'].iloc[0]}, MSRP: ${msrp:.2f}")
            
            # Find matching lease programs
            matches = lease_data[lease_data[model_column] == model_number]
            matches = matches[~matches[tier].isnull()]
            if matches.empty:
                st.error(f"No lease matches found for this tier.")
                return
            
            # Get available lease terms
            available_terms = sorted(matches["Term"].astype(float).unique(), key=lambda x: int(x))
            
            # Fixed fees and Q-value
            fixed_fees = 962.50  # Sum of acquisition, documentation, etc.
            q_value = 62.50  # Fee divided over the term
            
            # Process each term
            for term in available_terms:
                st.subheader(f"{int(term)}-Month Term")
                options = matches[matches["Term"] == term].copy()
                best = options.iloc[0]
                
                lease_cash = float(best.get("LeaseCash", 0.0))
                base_mf = float(best[tier])
                base_residual_pct = float(best["Residual"])
                term_months = int(term)
                
                # Display results for each mileage option
                mileage_cols = st.columns(3, gap="small")
                for i, mileage in enumerate(["10K", "12K", "15K"]):
                    # Check 10K mileage availability
                    if mileage == "10K" and not (33 <= term_months <= 48):
                        with mileage_cols[i]:
                            st.markdown(f"<div style='opacity:0.5'><h4>{mileage} Not Available</h4></div>", unsafe_allow_html=True)
                        continue
                    
                    # Adjust residual percentage based on mileage
                    residual_pct = base_residual_pct
                    if mileage == "10K":
                        residual_pct += 1
                    elif mileage == "15K":
                        residual_pct -= 2
                    residual_value = msrp * (residual_pct / 100)
                    
                    # Adjusted money factor
                    mf = base_mf + 0.0004
                    
                    # Calculate lease details
                    lease_details = calculate_lease_details(
                        ccr=ccr,
                        msrp=msrp,
                        lease_cash=lease_cash,
                        residual_value=residual_value,
                        term_months=term_months,
                        mf=mf,
                        county_tax=county_tax,
                        q_value=q_value,
                        fixed_fees=fixed_fees
                    )
                    
                    # Display results
                    with mileage_cols[i]:
                        st.markdown(f"""
                        <h4 style='color:#2e86de;'>${lease_details['Monthly_Payment']:.2f} / month</h4>
                        <p><b>Total Due at Signing:</b> ${lease_details['Total_DAS']:.2f}</p>
                        """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Something went wrong: {e}")
    else:
        st.info("Please enter a VIN and select a tier to begin.")

if __name__ == "__main__":
    main()
