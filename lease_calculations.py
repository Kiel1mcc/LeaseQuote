# lease_calculations.py

def calculate_ccr_full(SP, B, rebates, TV, K, M, Q, RES, F, W, τ):
    S = SP - TV
    U = 0.00
    bottomVal = (1 + τ) * (1 - (F + 1 / W)) - τ * F * (1 + F * W)

    # Initial TopVal Calculation
    topVal_initial = B - K - (
        F * (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U + RES) +
        (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U - RES) / W
    )

    debug_info = {
        "Initial TopVal": round(topVal_initial, 6),
        "Initial B": round(B, 2),
        "Initial S": round(S, 2),
        "K": round(K, 2),
        "M": round(M, 2),
        "Q": round(Q, 2),
        "RES": round(RES, 2),
        "F": round(F, 6),
        "W": W,
        "τ": round(τ, 6)
    }

    topVal = topVal_initial
    if topVal < 0:
        B += abs(topVal)
        topVal = B - K - (
            F * (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U + RES) +
            (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U - RES) / W
        )
        debug_info["Adjusted B"] = round(B, 2)
        debug_info["Adjusted TopVal"] = round(topVal, 6)

    CCR = topVal / bottomVal
    debug_info["CCR"] = round(CCR, 6)
    debug_info["BottomVal"] = round(bottomVal, 6)

    if CCR < 0:
        return 0.0, round(abs(CCR), 6), debug_info
    return round(CCR, 6), 0.0, debug_info

def calculate_payment_from_ccr(S, CCR, RES, W, F, τ, M):
    BP_initial = ((S + M - CCR - RES) / W) + ((S + M - CCR + RES) * F)
    ST = round(BP_initial * τ, 2)
    MP = round(BP_initial + ST, 2)

    return {
        "Base Payment (BP)": round(BP_initial, 2),
        "Sales Tax (ST)": ST,
        "Monthly Payment (MP)": MP,
        "Pre-Adjustment BP": round(BP_initial, 6),
        "Tax Rate (τ)": τ,
        "Term (W)": W,
        "Cap Cost Reduction (CCR)": CCR,
        "Net Cap Cost (S + M - CCR)": round(S + M - CCR, 2),
        "Residual (RES)": RES,
        "Money Factor (F)": round(F, 6),
        "Cap Cost (S + M)": round(S + M, 2),
        "Numerator (N)": round((S + M - CCR - RES) + (S + M - CCR + RES) * F, 6),
        "Denominator (D)": W
    }
