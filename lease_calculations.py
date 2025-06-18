# DO NOT import anything from lease_app.py here.
# This is a pure math module.

def calculate_base_and_monthly_payment(S, RES, W, F, M, Q, B, K, U, tau):
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

    BP = round(((S + M - CCR - RES) / W) + ((S + M - CCR + RES) * F), 2)
    ST = round(BP * tau, 2) * W
    TA = round(S + ST + M - CCR, 2)
    AMD = (TA - RES) / W
    ALC = F * (TA + RES)
    monthly_payment = round(AMD + ALC, 2)

    return {
        "Cap Cost Reduction": round(CCR, 2),
        "Total Advance": TA,
        "Average Monthly Depreciation": round(AMD, 2),
        "Average Lease Charge": round(ALC, 2),
        "Base Payment": BP,
        "Monthly Payment": monthly_payment,
        "Total Sales Tax": round(ST, 2),
    }
