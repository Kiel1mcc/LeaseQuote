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
        "Base Payment": BP,
        "Monthly Payment": round(monthly_payment, 2),
        "Cap Cost Reduction": round(CCR, 2),
        "Average Monthly Depreciation": round(AMD, 2),
        "Average Lease Charge": round(ALC, 2),
        "Total Advance": TA,
        "Total Sales Tax": ST
    }
