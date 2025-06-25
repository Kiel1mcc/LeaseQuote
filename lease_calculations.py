# lease_calculations.py

def calculate_ccr_full(SP, B, rebates, TV, K, M, Q, RES, F, W, τ):
    # Initialize variables
    U = 0.00
    cash_down = B  # Cash down payment from user
    lease_cash = rebates  # Lease cash or rebates
    total_incentives = cash_down + lease_cash + TV
    shortfall = 0.0
    applied_to_shortfall = 0.0
    remaining_cash_down = cash_down
    remaining_lease_cash = lease_cash
    remaining_trade_value = TV

    # Step 1: Calculate initial TopVal with B=0 and S=SP to find shortfall
    S = SP  # No trade value applied yet
    B_temp = 0.0  # Temporarily set B to 0
    bottomVal = (1 + τ) * (1 - (F + 1 / W)) - τ * F * (1 + F * W)

    topVal_initial = B_temp - K - (
        F * (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U + RES) +
        (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U - RES) / W
    )

    debug_info = {
        "Initial TopVal (B=0, S=SP)": round(topVal_initial, 6),
        "Initial B": round(B_temp, 2),
        "Initial S": round(S, 2),
        "Cash Down": round(cash_down, 2),
        "Lease Cash": round(lease_cash, 2),
        "Trade Value": round(TV, 2),
        "K": round(K, 2),
        "M": round(M, 2),
        "Q": round(Q, 2),
        "RES": round(RES, 2),
        "F": round(F, 6),
        "W": W,
        "τ": round(τ, 6)
    }

    # Step 2: Determine shortfall (dealership-covered amount)
    if topVal_initial < 0:
        shortfall = abs(topVal_initial)
        debug_info["Shortfall (Dealership Covered)"] = round(shortfall, 6)

        # Apply incentives to offset shortfall
        if shortfall > 0 and total_incentives > 0:
            applied_to_shortfall = min(shortfall, total_incentives)
            shortfall -= applied_to_shortfall

            # Distribute applied amount across incentives
            applied_cash_down = min(remaining_cash_down, applied_to_shortfall)
            remaining_cash_down -= applied_cash_down
            applied_to_shortfall -= applied_cash_down

            applied_lease_cash = min(remaining_lease_cash, applied_to_shortfall)
            remaining_lease_cash -= applied_lease_cash
            applied_to_shortfall -= applied_lease_cash

            applied_trade_value = min(remaining_trade_value, applied_to_shortfall)
            remaining_trade_value -= applied_trade_value

            debug_info["Applied to Shortfall"] = {
                "Total": round(applied_to_shortfall, 2),
                "Cash Down": round(applied_cash_down, 2),
                "Lease Cash": round(applied_lease_cash, 2),
                "Trade Value": round(applied_trade_value, 2)
            }
            debug_info["Remaining Incentives"] = {
                "Cash Down": round(remaining_cash_down, 2),
                "Lease Cash": round(remaining_lease_cash, 2),
                "Trade Value": round(remaining_trade_value, 2)
            }

        debug_info["Remaining Shortfall"] = round(shortfall, 6)

    # Step 3: Apply remaining incentives
    B = remaining_cash_down + remaining_lease_cash  # Down payment components
    S = SP - remaining_trade_value  # Apply trade value to sales price

    # Step 4: Adjust for dealership-covered shortfall
    # Add remaining shortfall to capitalized cost by increasing S
    S += shortfall

    # Step 5: Recalculate TopVal with updated B and S
    topVal = B - K - (
        F * (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U + RES) +
        (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U - RES) / W
    )

    debug_info["Final B"] = round(B, 2)
    debug_info["Final S (incl. Shortfall)"] = round(S, 2)
    debug_info["Final TopVal"] = round(topVal, 6)

    # Step 6: Calculate CCR
    CCR = topVal / bottomVal if bottomVal != 0 else 0.0
    overflow = 0.0

    if CCR < 0:
        CCR = 0.0
        overflow = abs(topVal / bottomVal) if bottomVal != 0 else 0.0

    debug_info["CCR"] = round(CCR, 6)
    debug_info["Overflow"] = round(overflow, 6)
    debug_info["BottomVal"] = round(bottomVal, 6)

    return round(CCR, 6), round(overflow, 6), debug_info

def calculate_payment_from_ccr(S, CCR, RES, W, F, τ, M, Q=0.0):
    cap_cost = S + M
    adjusted_cap_cost = cap_cost - CCR

    depreciation = (adjusted_cap_cost - RES) / W
    rent_charge = F * (adjusted_cap_cost + RES)
    BP = depreciation + rent_charge
    ST = (BP * τ) * W
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
