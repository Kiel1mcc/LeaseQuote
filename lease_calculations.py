def calculate_ccr(B, K, U, M, tau, F, W, S, RES):
    taxable_portion = S + M - U + RES
    flat_portion = S + M - U - RES

    topVal = (
        B - K
        - (
            F * (S + M + tau * (F * W * taxable_portion + flat_portion) - U + RES)
            + (S + M + tau * (F * W * taxable_portion + flat_portion) - U - RES) / W
        )
    )

    bottomVal = (1 + tau) * (1 - (F + 1 / W)) - (tau * F * (1 + F * W))

    CCR = topVal / bottomVal
    return CCR

def calculate_base_and_monthly_payment(S, RES, W, F, M, Q, B, K, U, tau):
    CCR = calculate_ccr(B, K, U, M, tau, F, W, S, RES)

    BP = round(((S + M - CCR - RES) / W) + ((S + M - CCR + RES) * F), 2)
    ST = round(BP * tau, 2) * W
    TA = round(S + ST + M - CCR, 2)
    AMD = (TA - RES) / W
    ALC = F * (TA + RES)
    monthly_payment = AMD + ALC

    return {
        "Base Payment": f"${BP:,.2f}",
        "Monthly Payment": f"${round(monthly_payment, 2):,.2f}",
        "Cap Cost Reduction": f"${round(CCR, 2):,.2f}",
        "Average Monthly Depreciation": f"${round(AMD, 2):,.2f}",
        "Average Lease Charge": f"${round(ALC, 2):,.2f}",
        "Total Advance": f"${TA:,.2f}",
        "Total Sales Tax": f"${ST:,.2f}"
    }
