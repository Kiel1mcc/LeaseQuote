# LOCKED FORMULA - CCR CALCULATION

def calculate_ccr_full(
    SP,  # Selling Price
    B,   # Cash Down + Lease Cash + Rebates
    rebates,
    TV,  # Trade Value
    K,   # Lease Inception Fees (not used directly)
    M,   # Taxable Fees (Doc + Acq)
    Q,   # Non-taxable Fees (License + Title)
    RES, # Residual Value ($)
    F,   # Money Factor
    W,   # Lease Term (Months)
    τ    # Sales Tax Rate
):
    """
    Calculate Cap Cost Reduction (CCR) using full Excel-style formula logic.
    Returns final CCR and any overflow amount to apply as cash down.

    FORMULA BELOW LOCKED — DO NOT EDIT BELOW UNLESS YOU ARE KIEL MCCLEARY
    """
    S = SP - TV  # Adjusted price after trade
    U = 0.00     # Non-cash CCR (if ever used)

    # LOCKED IN: Denominator (bottomVal)
    bottomVal = (1 + τ) * (1 - (F + 1 / W)) - τ * F * (1 + F * W)

    # LOCKED IN: Numerator (topVal)
    topVal = B - K - (
        F * (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U + RES) +
        (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U - RES) / W
    )

    if topVal < 0:
        B += abs(topVal)
        # Recalculate numerator with updated B
        topVal = B - K - (
            F * (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U + RES) +
            (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U - RES) / W
        )

    CCR = topVal / bottomVal

    if CCR < 0:
        return 0.0, round(abs(CCR), 6)
    else:
        return round(CCR, 6), 0.0

def calculate_payment_from_ccr(
    SP,
    CCR,
    RES,
    W,
    F,
    τ,
    M=900.0,  # DOC + ACQ default
    Q=62.50   # License + Title default
):
    """FORMULA ABOVE LOCKED — DO NOT EDIT BELOW UNLESS YOU ARE KIEL MCCLEARY
      Compute base payment, tax, and monthly lease payment.
    Includes safeguard: if numerator is negative, it is inverted.
    """
    cap_cost = (SP - CCR) + M
    numerator = (cap_cost - RES) + (cap_cost + RES) * F

    if numerator < 0:
        numerator = abs(numerator)

    depreciation = (cap_cost - RES) / W
    rent_charge = F * (cap_cost + RES)
    BP = depreciation + rent_charge

    monthly_tax = BP * τ
    MP = BP + monthly_tax
    ST = monthly_tax * W

    return {
        "Base Payment (BP)": round(BP, 2),
        "Monthly Payment (MP)": round(MP, 2),
        "Sales Tax (ST)": round(ST, 2),
        "Depreciation (AMD)": round(depreciation, 2),
        "Lease Charge (ALC)": round(rent_charge, 2),
        "Net Cap Cost (TA)": round(cap_cost, 2),
        "Numerator (N)": round(numerator, 6),
        "Denominator (D)": W
    }

# Glossary reference:
# SP = Sales Price
# TV = Trade Value
# B = Cash Down + Lease Cash + Rebates
# M = Taxable Fees (DOC + ACQ)
# Q = Non-taxable Fees (License + Title)
# RES = Residual Value ($)
# F = Money Factor
# W = Lease Term
# τ = Sales Tax Rate
# U = Non-cash CCR (unused but placeholder for formula compatibility)
