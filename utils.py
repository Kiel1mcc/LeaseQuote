from lease_calculations import calculate_ccr_full, calculate_payment_from_ccr


def calculate_option_payment(selling_price: float, lease_cash_used: float, residual_value: float,
                             money_factor: float, term: int, trade_val: float,
                             cash_down: float, tax_rt: float) -> dict:
    """Return payment data for a lease option."""
    initial_B = lease_cash_used
    ccr_initial, _, debug_ccr_initial = calculate_ccr_full(
        SP=selling_price, B=initial_B, rebates=0.0, TV=0.0, K=0.0, M=962.50, Q=0.0,
        RES=residual_value, F=money_factor, W=term, τ=tax_rt
    )
    overflow = abs(debug_ccr_initial.get("Initial TopVal", 0.0)) if debug_ccr_initial.get("Initial TopVal", 0.0) < 0 else 0
    trade_used = min(trade_val, overflow)
    remaining_gap = overflow - trade_used
    cash_used = min(cash_down, remaining_gap)
    remaining_trade = trade_val - trade_used
    remaining_cash = cash_down - cash_used
    adjusted_SP = selling_price - remaining_trade
    total_B = initial_B + trade_used + cash_used + remaining_cash
    ccr, _, _ = calculate_ccr_full(
        SP=adjusted_SP, B=total_B, rebates=0.0, TV=0.0, K=0.0, M=962.50, Q=0.0,
        RES=residual_value, F=money_factor, W=term, τ=tax_rt
    )
    payment = calculate_payment_from_ccr(
        S=adjusted_SP, CCR=ccr, RES=residual_value, W=term,
        F=money_factor, τ=tax_rt, M=962.50, Q=0.0
    )
    return {
        'payment': payment['Monthly Payment (MP)'],
        'base_payment': payment['Base Payment (BP)'],
        'tax_payment': payment['Sales Tax (ST)'],
        'ccr': ccr,
        'trade_used': trade_used,
        'remaining_cash': remaining_cash
    }


def sort_quote_options(options, sort_by, trade_value, cash_down, tax_rate):
    """Return filtered and sorted list of quote options."""
    sort_options = {
        "Lowest Payment": "payment",
        "Lowest Term": "term",
        "Lowest Mileage": "mileage",
        "Most Lease Cash Available": "available_lease_cash",
    }

    if sort_by == "Most Lease Cash Available":
        options.sort(key=lambda x: x['available_lease_cash'], reverse=True)
    elif sort_by == "Lowest Payment":
        options.sort(key=lambda x: calculate_option_payment(
            x['selling_price'], x['lease_cash_used'], x['residual_value'],
            x['money_factor'], x['term'], trade_value, cash_down, tax_rate
        )['payment'])
    else:
        options.sort(key=lambda x: x[sort_options[sort_by]])

    return options
