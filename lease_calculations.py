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

def calculate_payment_from_ccr(S, CCR, RES, W, F, τ, M):
    BP = ((S + M - CCR - RES) / W) + ((S + M - CCR + RES) * F)
    ST = round(BP * τ, 2)
    MP = round(BP + ST, 2)
    return {
        "Base Payment (BP)": round(BP, 2),
        "Sales Tax (ST)": ST,
        "Monthly Payment (MP)": MP
    }
