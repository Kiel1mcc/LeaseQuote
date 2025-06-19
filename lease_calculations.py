def calculate_ccr_full(
    selling_price,
    money_down,
    lease_cash_used,
    rebates,
    trade_value,
    doc_fee,
    acq_fee,
    license_fee,
    title_fee,
    residual_value,
    money_factor,
    term,
    tax_rate
):
    """
    Calculate Cap Cost Reduction (CCR) with overflow logic for negative values.

    Returns:
    - final_ccr: float — the usable cap cost reduction (≥ 0)
    - overflow_down: float — if CCR < 0, this is added as extra cash down
    """

    adjusted_price = selling_price - trade_value
    M = doc_fee + acq_fee
    Q = license_fee + title_fee

    credits = money_down + lease_cash_used + rebates

    # New logic — no longer using tax or base payment here
    ccr = credits - M - Q

    if ccr >= 0:
        return round(ccr, 2), 0.0
    else:
        overflow = round(abs(ccr), 2)
        return 0.0, overflow

def calculate_payment_from_ccr(
    selling_price,
    cap_cost_reduction,
    residual_value,
    term,
    money_factor,
    tax_rate,
    doc_fee=250.0,
    acq_fee=650.0,
    license_fee=47.50,
    title_fee=15.0
):
    """
    Compute base payment, monthly payment, and sales tax
    from the final CCR produced by `calculate_ccr_full`.
    Returns a dict with human-readable values.
    """
    taxable_fees = doc_fee + acq_fee
    net_cap_cost = (selling_price - cap_cost_reduction) + taxable_fees
    depreciation = (net_cap_cost - residual_value) / term
    rent_charge = money_factor * (net_cap_cost + residual_value)
    base_payment = depreciation + rent_charge

    monthly_tax = base_payment * tax_rate
    monthly_payment = base_payment + monthly_tax

    total_sales_tax = monthly_tax * term

    return {
        "Base Payment": round(base_payment, 2),
        "Monthly Payment": round(monthly_payment, 2),
        "Total Sales Tax": round(total_sales_tax, 2),
    }

# Example usage:
# ccr, overflow = calculate_ccr_full(
#     selling_price=25040,
#     money_down=0,
#     lease_cash_used=1500,
#     rebates=0,
#     trade_value=0,
#     doc_fee=250,
#     acq_fee=650,
#     license_fee=47.50,
#     title_fee=15.0,
#     residual_value=15000,
#     money_factor=0.00100,
#     term=36,
#     tax_rate=0.0725
# )
