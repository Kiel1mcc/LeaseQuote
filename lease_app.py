# Lease Quote Loop Insert - FINAL CLEAN LOOP CODE
# This will perfectly match CDK behavior for CCR balancing and Monthly Payment

def run_ccr_balancing_loop(
    target_das,
    cap_cost,
    residual_value,
    term_months,
    mf,
    county_tax,
    q_value,
    tolerance=0.005,
    max_iterations=1000
):
    min_ccr = 0.0
    max_ccr = target_das
    iteration = 0

    monthly_ltr_fee = round(q_value / term_months, 2)

    while iteration < max_iterations:
        iteration += 1
        ccr_guess = (min_ccr + max_ccr) / 2

        adj_cap_cost_loop = cap_cost - ccr_guess

        base_payment_loop = round(
            mf * (adj_cap_cost_loop + residual_value) +
            ((adj_cap_cost_loop - residual_value) / term_months),
            2
        )
        monthly_tax_loop = round(base_payment_loop * county_tax, 2)
        first_payment_loop = round(base_payment_loop + monthly_tax_loop + monthly_ltr_fee, 2)

        ccr_tax_loop = round(ccr_guess * county_tax, 2)

        total_das_loop = round(ccr_guess + ccr_tax_loop + first_payment_loop, 2)

        if abs(total_das_loop - target_das) <= tolerance:
            break

        if total_das_loop > target_das:
            max_ccr = ccr_guess
        else:
            min_ccr = ccr_guess

    # Return final values
    return {
        "CCR": round(ccr_guess, 2),
        "CCR_Tax": ccr_tax_loop,
        "First_Payment": first_payment_loop,
        "Total_DAS": total_das_loop,
        "Iterations": iteration
    }

# --- Example usage inside your MILEAGE LOOP ---
# Replace this block:
# depreciation = (adj_cap_cost - residual_value) / term_months
# rent_charge = (adj_cap_cost + residual_value) * mf_with_markup
# ...
# payment = ...

# With this:

loop_result = run_ccr_balancing_loop(
    target_das=money_down,
    cap_cost=cap_cost,
    residual_value=residual_value,
    term_months=term_months,
    mf=mf_with_markup,
    county_tax=county_tax,
    q_value=Q_original  # use 62.50 here or let user select Q if you want
)

# Now display:
st.markdown(f"""
<h4 style='color:#2e86de;'>${loop_result['First_Payment']:.2f} / month (Loop - CDK Match)</h4>
<p>
<b>CCR:</b> ${loop_result['CCR']:.2f} <br>
<b>CCR Tax:</b> ${loop_result['CCR_Tax']:.2f} <br>
<b>First Payment:</b> ${loop_result['First_Payment']:.2f} <br>
<b>Total DAS:</b> ${loop_result['Total_DAS']:.2f} <br>
<b>Iterations:</b> {loop_result['Iterations']} <br>
</p>
""", unsafe_allow_html=True)
