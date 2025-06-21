# lease_calculations.py

def calculate_ccr_full(SP, B, rebates, TV, K, M, Q, RES, F, W, τ, adjust_negative=True):

    """Calculate the capitalized cost reduction (CCR) needed for a lease.

    Parameters
    ----------
    SP : float
        Selling price of the vehicle.
    B : float
        Initial cash applied toward CCR.
    rebates : float
        Placeholder for manufacturer rebates (currently unused).
    TV : float
        Trade-in value to reduce the selling price.
    K : float
        Upfront fees paid in cash.
    M : float
        Additional charges to be capitalized.
    Q : float
        Upfront taxes or fees added to the lease balance.
    RES : float
        Residual value of the vehicle.
    F : float
        Money factor.
    W : int
        Lease term in months.
    τ : float
        Sales tax rate expressed as a decimal.
    adjust_negative : bool, optional
        When ``True`` (default), any negative ``topVal`` is absorbed by
        increasing ``B`` before calculating CCR. When ``False`` the raw
        negative ``topVal`` is used, allowing callers to inspect it.

    Returns
    -------
    tuple
        ``(CCR, overflow, debug_info)`` where ``CCR`` is the calculated
        cap cost reduction, ``overflow`` is the absolute value of a
        negative CCR (``0.0`` otherwise), and ``debug_info`` contains
        intermediate calculation values.
    """

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

    if topVal < 0 and adjust_negative:

    if adjust_negative and topVal < 0:

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

def calculate_payment_from_ccr(S, CCR, RES, W, F, τ, M, Q=0.0):
    cap_cost = S + M
    adjusted_cap_cost = cap_cost - CCR

    depreciation = (adjusted_cap_cost - RES) / W
    rent_charge = F * (adjusted_cap_cost + RES)
    BP =  depreciation + rent_charge
    ST = (BP * τ)* W
    TA = S + Q + ST + M - CCR
    AMD = (TA - RES) / W
    ALC = F * (TA + RES)
    MP = AMD + ALC

    return {
        "Base Payment (BP)": round(BP, 2),
        "Sales Tax (ST)": round(ST, 2),
        "Monthly Payment (MP)": round(MP, 2),
        "Pre-Adjustment BP": round(BP, 6),
        "Depreciation": round(depreciation, 6),
        "Rent Charge": round(rent_charge, 6),
        "Tax Rate (τ)": τ,
        "Term (W)": W,
        "Cap Cost Reduction (CCR)": CCR,
        "Residual (RES)": RES,
        "Money Factor (F)": round(F, 6),
        "Net Cap Cost (S + M - CCR)": round(adjusted_cap_cost, 2),
        "Cap Cost (S + M)": round(cap_cost, 2),
        "Tax Calculation": f"{round(BP, 6)} * {round(τ, 6)} = {round(ST, 6)}"
    }
