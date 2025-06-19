# lease_calculations.py

def calculate_ccr_full(SP, B, rebates, TV, K, M, Q, RES, F, W, τ):
    S = SP - TV
    U = 0.00
    bottomVal = (1 + τ) * (1 - (F + 1 / W)) - τ * F * (1 + F * W)
    topVal = B - K - (
        F * (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U + RES) +
        (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U - RES) / W
    )
    if topVal < 0:
        B += abs(topVal)
        topVal = B - K - (
            F * (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U + RES) +
            (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U - RES) / W
        )
    CCR = topVal / bottomVal
    if CCR < 0:
        return 0.0, round(abs(CCR), 6)
    return round(CCR, 6), 0.0

def calculate_payment_from_ccr(SP, CCR, RES, W, F, τ, M=900.0, Q=62.50):
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
