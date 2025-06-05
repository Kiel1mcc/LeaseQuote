mileage_cols = st.columns(3)
mile_data = []

for i, mileage in enumerate(["10K", "12K", "15K"]):
    term_months = int(term)

    # 10K is only valid for 33–48 month terms
    if mileage == "10K" and not (33 <= term_months <= 48):
        mile_data.append((mileage, None, True))
        continue

    # Adjust residual percentage based on mileage
    mileage_upper = mileage.upper()
    if mileage_upper == "12K":
        residual_pct = base_residual_pct
    elif mileage_upper == "10K":
        residual_pct = base_residual_pct + 1
    elif mileage_upper == "15K":
        residual_pct = base_residual_pct - 2
    else:
        residual_pct = base_residual_pct  # fallback

    # Calculate lease values
    residual = msrp * (residual_pct / 100)
    cap_cost = msrp - rebate - money_down
    rent = (cap_cost + residual) * mf * term_months
    depreciation = cap_cost - residual
    base_monthly = (depreciation + rent) / term_months
    tax = base_monthly * county_tax
    total_monthly = base_monthly + tax

    mile_data.append((mileage, total_monthly, False))
