def calculate_base_and_monthly_payment(SP, B, rebates, TV, K, M, Q, RES, F, W, τ):
    # Step 1: Cap Cost Reduction
    CCR = B + rebates

    # Step 2: Cap Cost
    cap_cost = SP + M + Q - CCR - TV

    # Step 3: Depreciation
    depreciation = cap_cost - RES

    # Step 4: Rent Charge
    rent_charge = (cap_cost + RES) * F

    # Step 5: Base Payment
    base_payment = depreciation / W + rent_charge

    # Step 6: Tax on Monthly Payment
    tax_amount = base_payment * τ

    # Step 7: Final Monthly Payment
    monthly_payment = round(base_payment + tax_amount, 2)

    debug_info = {
        "Base Payment": round(base_payment, 2),
        "Tax Amount": round(tax_amount, 2),
        "Monthly Payment": monthly_payment,
        "CCR": CCR,
    }

    return CCR, monthly_payment, debug_info

def calculate_ccr_full(SP, B, rebates, TV, K, M, Q, RES, F, W, τ, adjust_negative):
    # Step 1: Cap Cost Reduction
    CCR = B + rebates

    # Step 2: Cap Cost
    cap_cost = SP + M + Q - CCR - TV

    # Step 3: Depreciation
    depreciation = cap_cost - RES

    # Step 4: Rent Charge
    rent_charge = (cap_cost + RES) * F

    # Step 5: Base Payment
    base_payment = depreciation / W + rent_charge

    # Step 6: Tax on Monthly Payment
    tax_amount = base_payment * τ

    # Step 7: Final Monthly Payment
    monthly_payment = round(base_payment + tax_amount, 2)

    # Step 8: TopVal (represents remaining uncovered amount)
    topval = (base_payment + tax_amount) - (B + TV + rebates)

    if adjust_negative and topval < 0:
        topval = 0.0

    debug_info = {
        "Base Payment": round(base_payment, 2),
        "Tax Amount": round(tax_amount, 2),
        "Monthly Payment": monthly_payment,
        "CCR": CCR,
        "Initial TopVal": topval,
    }

    return CCR, monthly_payment, debug_info
