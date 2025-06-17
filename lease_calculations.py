def calculate_payment(
    msrp: float,
    money_factor: float,
    residual_pct: float,
    term: int,
    mileage: int,
    tax_rate: float,
    money_down: float,
    rebate: float,
) -> dict:
    """
    Simplified lease payment formula:
      - Depreciation = (Cap Cost – Residual) / Term
      - Finance Charge = (Cap Cost + Residual) * MF
      - Base Payment = Depreciation + Finance Charge
      - Sales Tax = Base Payment * tax_rate
      - Monthly Payment = Base Payment + Sales Tax
    """
    residual_value = msrp * residual_pct
    cap_cost = msrp - rebate + money_down

    depreciation = (cap_cost - residual_value) / term
    finance_charge = (cap_cost + residual_value) * money_factor
    base_payment = depreciation + finance_charge
    sales_tax = base_payment * tax_rate
    monthly_payment = base_payment + sales_tax

    return {
        "Residual Value": round(residual_value, 2),
        "Capitalized Cost": round(cap_cost, 2),
        "Depreciation": round(depreciation, 2),
        "Finance Charge": round(finance_charge, 2),
        "Base Payment": round(base_payment, 2),
        "Monthly Sales Tax": round(sales_tax, 2),
        "Monthly Payment": round(monthly_payment, 2),
    }
