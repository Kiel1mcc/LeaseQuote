import streamlit as st

st.title("Motor Vehicle Lease Calculator")

# Input fields for lease parameters
st.header("Lease Parameters")
msrp = st.number_input("MSRP ($)", min_value=0.0, value=52640.00, step=100.0)
dealer_discount = st.number_input("Dealer Discount ($)", min_value=0.0, value=5000.00, step=100.0)
acquisition_fee = st.number_input("Acquisition Fee ($)", min_value=0.0, value=650.00, step=10.0)
doc_fee = st.number_input("Doc Fee ($)", min_value=0.0, value=85.00, step=10.0)
total_rebates = st.number_input("Total Rebates/Credits/Incentives ($)", min_value=0.0, value=14000.00, step=100.0)
gov_fees = st.number_input("Gov Fees - License/Title/Reg ($)", min_value=0.0, value=653.00, step=10.0)
sales_tax_rate = st.number_input("Sales Tax Rate (%)", min_value=0.0, value=8.375, step=0.1) / 100
money_factor = st.number_input("Money Factor", min_value=0.0, value=0.00161, step=0.00001)
term = st.number_input("Term (Months)", min_value=1, value=24, step=1)
residual_factor = st.number_input("Residual Factor (%)", min_value=0.0, value=58.0, step=1.0) / 100
non_cash_ccr = st.number_input("Non-Cash CCR Credits ($, e.g., Trade Equity)", min_value=0.0, value=0.0, step=100.0)

# Calculations
sell_price = msrp - dealer_discount
gross_cap_cost = sell_price + acquisition_fee + doc_fee
residual_value = msrp * residual_factor
taxable_cap_fees = acquisition_fee + doc_fee

# CCR Calculation
# CCR = (C - K - (1 + τ) * [F * (S + M - U + R) + (S + M - U - R) / N]) / ((1 + τ) * [1 - (F + 1/N)])
numerator = total_rebates - gov_fees - (1 + sales_tax_rate) * (
    money_factor * (sell_price + taxable_cap_fees - non_cash_ccr + residual_value) +
    (sell_price + taxable_cap_fees - non_cash_ccr - residual_value) / term
)
denominator = (1 + sales_tax_rate) * (1 - (money_factor + 1 / term))
ccr = numerator / denominator if denominator != 0 else 0

adjusted_cap_cost = gross_cap_cost - ccr

# Monthly Payment Calculations
monthly_base_payment = (
    money_factor * (adjusted_cap_cost + residual_value) +
    (adjusted_cap_cost - residual_value) / term
)
monthly_lease_payment = monthly_base_payment * (1 + sales_tax_rate)

# Lease Inception Fees
ccr_tax = ccr * sales_tax_rate
total_inception_fees = monthly_lease_payment + ccr + ccr_tax + gov_fees
amount_due_at_signing = max(0, total_inception_fees - total_rebates)

# Display Results
st.header("Lease Calculation Results")
st.subheader("Capitalized Costs")
st.write(f"Sell Price: ${sell_price:,.2f}")
st.write(f"Gross Capitalized Cost: ${gross_cap_cost:,.2f}")
st.write(f"Capitalized Cost Reduction (CCR): ${ccr:,.2f}")
st.write(f"Adjusted Capitalized Cost: ${adjusted_cap_cost:,.2f}")

st.subheader("Residual and Term")
st.write(f"Residual Value: ${residual_value:,.2f}")
st.write(f"Term: {term} months")
st.write(f"Money Factor: {money_factor:.5f}")

st.subheader("Payments")
st.write(f"Monthly Base Payment: ${monthly_base_payment:,.2f}")
st.write(f"Monthly Lease Payment (with {sales_tax_rate*100:.3f}% tax): ${monthly_lease_payment:,.2f}")

st.subheader("Lease Inception Fees")
st.write(f"First Payment: ${monthly_lease_payment:,.2f}")
st.write(f"CCR Partial Rebate: ${ccr:,.2f}")
st.write(f"CCR Sales Tax: ${ccr_tax:,.2f}")
st.write(f"Gov Fees: ${gov_fees:,.2f}")
st.write(f"Total Inception Fees: ${total_inception_fees:,.2f}")
st.write(f"Rebates/Credits Applied: ${total_rebates:,.2f}")
st.write(f"Amount Due at Signing: ${amount_due_at_signing:,.2f}")

st.write(f"**Bottom Line**: ${amount_due_at_signing:,.2f} due at signing, followed by {term-1} monthly payments of ${monthly_lease_payment:,.2f} each.")
