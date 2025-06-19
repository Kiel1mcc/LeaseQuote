
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

    # 1. Adjusted selling price if trade is used
    adjusted_price = selling_price - trade_value

    # 2. Fees and costs
    M = doc_fee + acq_fee
    Q = license_fee + title_fee
    tau = tax_rate

    # 3. Credits that reduce cap cost
    credits = money_down + lease_cash_used + rebates

    # 4. Base payment before tax
    depreciation = adjusted_price - residual_value
    rent_charge = (adjusted_price + residual_value) * money_factor
    base_payment = (depreciation + rent_charge) / term

    # 5. Cap cost reduction calculation
    ccr = credits - M - Q - (tau * base_payment)

    if ccr >= 0:
        return round(ccr, 2), 0.0
    else:
        overflow = round(abs(ccr), 2)
        return 0.0, overflow
