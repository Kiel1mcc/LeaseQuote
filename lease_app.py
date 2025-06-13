import streamlit as st
import pandas as pd
import re

# Load data files with error handling
try:
    lease_data = pd.read_csv("All_Lease_Programs_Database.csv")
    lease_data.columns = lease_data.columns.str.strip()
except FileNotFoundError:
    st.error("Lease data file 'All_Lease_Programs_Database.csv' not found.")
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
    county_df["Dropdown_Label"] = county_df["County"] + " (" + county_df["Tax Rate"].astype(str) + "% )"
except FileNotFoundError:
    st.error("County tax rates file 'County_Tax_Rates.csv' not found.")
    st.stop()

try:
    locator_data = pd.read_excel("Locator_Detail_20250605.xlsx", dtype={"MSRP": str})
    locator_data.columns = locator_data.columns.str.strip()
    locator_data["VIN"] = (locator_data["VIN"].astype(str)
                         .str.strip()
                         .str.upper()
                         .str.replace("\u200b", "")
                         .str.replace("\ufeff", ""))
except FileNotFoundError:
    st.error("Locator data file 'Locator_Detail_20250605.xlsx' not found.")
    st.stop()

def run_ccr_balancing_loop(target_das, msrp, lease_cash, residual_value, term_months, mf, county_tax, q_value, tolerance=0.005, max_iterations=1000):
    min_ccr = 0.0
    max_ccr = msrp - residual_value - 500  # proper upper bound
    iteration = 0

    fixed_fees = 250.00 + 650.00 + 15.00 + 47.50
    cap_cost = msrp  # FIXED HERE, no longer subtracting lease_cash

    while iteration < max_iterations:
        iteration += 1
        ccr_guess = (min_ccr + max_ccr) / 2

        adj_cap_cost_loop = cap_cost - ccr_guess

        monthly_depreciation = (adj_cap_cost_loop - residual_value) / term_months
        monthly_rent_charge = (adj_cap_cost_loop + residual_value) * mf

        base_payment_loop_exact = monthly_depreciation + monthly_rent_charge

        monthly_tax_loop = round(base_payment_loop_exact * county_tax, 2)

        ltr_fee_upfront = 62.50
        ltr_fee_tax = round(ltr_fee_upfront * county_tax, 2)

        first_month_payment = round(base_payment_loop_exact + monthly_tax_loop, 2)

        first_payment_loop = round(first_month_payment, 2)

        ccr_tax_loop = round(ccr_guess * county_tax, 2)

        total_das_loop = round(ccr_guess + ccr_tax_loop + first_payment_loop + fixed_fees, 2)

        if abs(total_das_loop - target_das) <= tolerance:
            break

        if total_das_loop > target_das:
            max_ccr = ccr_guess
        else:
            min_ccr = ccr_guess

    return {
        "CCR": round(ccr_guess, 2),
        "CCR_Tax": ccr_tax_loop,
        "First_Payment": first_payment_loop,
        "First_Month_Payment": first_month_payment,
        "Total_DAS": total_das_loop,
        "Iterations": iteration
    }

def main():
    st.title("Lease Quote Calculator")

    vin = st.text_input("Enter VIN:", help="VIN will be converted to uppercase for matching").strip().upper()
    tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
    selected_county = st.selectbox("Select County:", county_df["Dropdown_Label"])
    county_tax = county_df[county_df["Dropdown_Label"] == selected_county]["Tax Rate"].values[0] / 100

    money_down = st.number_input("Down Payment ($)", value=0.0, min_value=0.0, help="Enter total amount the customer is putting down")

    st.markdown("""
    **Calculation Details:**
    - **Down Payment:** What the customer is putting down.
    - **Loop will solve for:** CCR, CCR Tax, First Payment to exactly match Down Payment (Total DAS).
    """)

    if vin and tier:
        try:
            msrp_row = locator_data[locator_data["VIN"] == vin]
            if msrp_row.empty:
                st.error(f"VIN '{vin}' not found in locator file.")
                return

            model_number = msrp_row["ModelNumber"].iloc[0].strip().upper()
            model_number = re.sub(r'[^\x20-\x7E]', '', model_number)

            msrp_str = str(msrp_row["MSRP"].iloc[0])
            msrp = float(msrp_str.replace('$', '').replace(',', ''))

            st.write(f"Vehicle: {msrp_row['Model'].iloc[0]} {msrp_row['Trim'].iloc[0]}, MSRP: ${msrp:.2f}")

            matches = lease_data[lease_data[model_column] == model_number]
            matches = matches[~matches[tier].isnull()]
            if matches.empty:
                st.error(f"No lease matches found for this tier.")
                return

            available_terms = sorted(matches["Term"].astype(float).unique(), key=lambda x: int(x))

            q_value = 62.50

            for term in available_terms:
                st.subheader(f"{int(term)}-Month Term")
                options = matches[matches["Term"] == term].copy()
                best = options.iloc[0]

                lease_cash = float(best.get("LeaseCash", 0.0))
                base_mf = float(best[tier])
                base_residual_pct = float(best["Residual"])
                term_months = int(term)

                residual_value = msrp * (base_residual_pct / 100)

                remove_markup = st.toggle("Remove Markup", False, key=f"markup_{term}")
                mf_to_use = base_mf if remove_markup else base_mf + 0.0004

                loop_result = run_ccr_balancing_loop(
                    target_das=money_down,
                    msrp=msrp,
                    lease_cash=lease_cash,
                    residual_value=residual_value,
                    term_months=term_months,
                    mf=mf_to_use,
                    county_tax=county_tax,
                    q_value=q_value
                )

                st.markdown(f"""
                <h4 style='color:#2e86de;'>${loop_result['First_Month_Payment']:.2f} / month</h4>
                <p>
                <b>MF used:</b> {mf_to_use} <br>
                <b>Residual % used:</b> {base_residual_pct}% <br>
                <b>CCR:</b> ${loop_result['CCR']:.2f} <br>
                <b>CCR Tax:</b> ${loop_result['CCR_Tax']:.2f} <br>
                <b>First Payment:</b> ${loop_result['First_Payment']:.2f} <br>
                <b>Total DAS:</b> ${loop_result['Total_DAS']:.2f} <br>
                <b>Iterations:</b> {loop_result['Iterations']} <br>
                <b>--- Debug Variables ---</b> <br>
                <b>C (Rebates/LeaseCash):</b> ${lease_cash:.2f} <br>
                <b>K (Fixed Fees):</b> $962.50 <br>
                <b>U:</b> $0.00 <br>
                <b>M (Taxable Fees):</b> $0.00 <br>
                <b>Q (LTR Fee):</b> ${q_value:.2f} <br>
                <b>Tax Rate:</b> {county_tax * 100:.2f}% <br>
                <b>F (MF used):</b> {mf_to_use} <br>
                <b>N (Term):</b> {term_months} <br>
                <b>S (MSRP):</b> ${msrp:.2f} <br>
                <b>R (Residual Value):</b> ${residual_value:.2f} <br>
                </p>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Something went wrong: {e}")
    else:
        st.info("Please enter a VIN and select a tier to begin.")

if __name__ == "__main__":
    main()
