
def calculate_ccr_full(
    selling_price,
    trade_value,
    credits,
    inception_fees,
    non_cash_ccr,
    taxable_fees,
    nontaxable_fees,
    tax_rate,
    money_factor,
    term_months,
    residual_value
):
    adjusted_selling_price = selling_price - trade_value

    def compute_ccr(cash_input):
        part1 = money_factor * term_months
        part2 = adjusted_selling_price + taxable_fees - non_cash_ccr + residual_value
        part3 = adjusted_selling_price + taxable_fees - non_cash_ccr - residual_value

        return (
            cash_input
            - inception_fees
            - (
                money_factor * (
                    adjusted_selling_price
                    + taxable_fees
                    + nontaxable_fees
                    + tax_rate * (part1 * part2 + part3)
                )
                - non_cash_ccr
                + residual_value
            )
            + (
                (
                    adjusted_selling_price
                    + taxable_fees
                    + nontaxable_fees
                    + tax_rate * (part1 * part2 + part3)
                    - non_cash_ccr
                    - residual_value
                ) / term_months
            )
        )

    initial_ccr = compute_ccr(credits)

    if initial_ccr < 0:
        adjusted_cash_down = abs(initial_ccr)
        final_ccr = compute_ccr(adjusted_cash_down)
        return {
            "Adjusted_Selling_Price": adjusted_selling_price,
            "CCR": 0.0,
            "Adjusted_Cash_Down": adjusted_cash_down,
            "Recalculated_CCR": final_ccr
        }
    else:
        return {
            "Adjusted_Selling_Price": adjusted_selling_price,
            "CCR": initial_ccr,
            "Adjusted_Cash_Down": 0.0,
            "Recalculated_CCR": initial_ccr
        }

def calculate_payment_from_ccr(
    selling_price,
    cap_cost_reduction,
    residual_value,
    term_months,
    money_factor,
    tax_rate,
    taxable_fees=962.50,
    nontaxable_fees=0.0
):
    net_cap = selling_price + taxable_fees - cap_cost_reduction
    depreciation = (net_cap - residual_value) / term_months
    lease_charge = money_factor * (net_cap + residual_value)
    base_payment = depreciation + lease_charge
    total_tax = base_payment * tax_rate * term_months
    total_advance = selling_price + total_tax + taxable_fees - cap_cost_reduction
    average_monthly_depreciation = (total_advance - residual_value) / term_months
    average_lease_charge = money_factor * (total_advance + residual_value)
    monthly_payment = average_monthly_depreciation + average_lease_charge

    return {
        "Cap Cost Reduction": cap_cost_reduction,
        "Total Advance": total_advance,
        "Average Monthly Depreciation": average_monthly_depreciation,
        "Average Lease Charge": average_lease_charge,
        "Base Payment": base_payment,
        "Monthly Payment": monthly_payment,
        "Total Sales Tax": total_tax,
    }
