def calculate_payment_from_ccr(
    selling_price,
    cap_cost_reduction,
    residual_value,
    term,
    money_factor,
    tax_rate,
    doc_fee=595.0,
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
