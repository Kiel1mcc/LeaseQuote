import streamlit as st
import pandas as pd
from lease_calculations import calculate_ccr_full, calculate_payment_from_ccr

st.set_page_config(page_title="Lease Quote Tool", layout="wide")

# Load data
lease_programs = pd.read_csv("All_Lease_Programs_Database.csv", encoding="utf-8-sig")
lease_programs.columns = lease_programs.columns.str.strip()

vehicle_data = pd.read_excel("Locator_Detail_Updated.xlsx")
vehicle_data.columns = vehicle_data.columns.str.strip()

# Sidebar inputs
with st.sidebar:
    st.header("Lease Parameters")
    vin_input = st.text_input("Enter VIN:", "")
    selected_tier = st.selectbox("Select Tier:", [f"Tier {i}" for i in range(1, 9)])
    selected_county = st.selectbox("Select County:", ["Adams", "Franklin", "Marion"])
    trade_value_input = st.number_input("Trade Value ($)", min_value=0.0, value=0.0, step=100.0)
    default_money_down = st.number_input("Default Down Payment ($)", min_value=0.0, value=0.0, step=100.0)
    apply_markup = st.checkbox("Apply Money Factor Markup (+0.0004)", value=False)

# VIN match
if vin_input:
    vin_data = vehicle_data[vehicle_data["VIN"] == vin_input]
    if vin_data.empty:
        st.warning("Vehicle not found in inventory.")
    else:
        vehicle = vin_data.iloc[0]
        model_number = vehicle["ModelNumber"]
        msrp = vehicle["MSRP"]

        lease_matches = lease_programs[lease_programs["ModelNumber"] == model_number]
        if lease_matches.empty:
            st.error("No lease program found for this model number.")
        else:
            lease_info = lease_matches.iloc[0]
            model_year = lease_info.get("Year", "N/A")
            make = lease_info.get("Make", "Hyundai")
            model = lease_info.get("Model", "N/A")
            trim = lease_info.get("Trim", "N/A")

            st.markdown(f"### Vehicle: {model_year} {make} {model} {trim} — MSRP: ${msrp:,.2f}")

            tier_num = int(selected_tier.split(" ")[1])
            tax_rate = 0.0725
            mileage_options = [10000, 12000, 15000]
            lease_terms = sorted(lease_matches["Term"].dropna().unique())

            for term in lease_terms:
                term_group = lease_matches[lease_matches["Term"] == term]
                st.subheader(f"{term}-Month Lease")

                for mileage in mileage_options:
                    row = term_group.iloc[0]
                    base_residual = float(row["Residual"])
                    adjusted_residual = base_residual + 0.01 if mileage == 10000 else base_residual - 0.02 if mileage == 15000 else base_residual
                    residual_value = round(msrp * adjusted_residual, 2)

                    mf_col = f"Tier {tier_num}"
                    money_factor = float(row[mf_col])
                    if apply_markup:
                        money_factor += 0.0004
                    available_lease_cash = float(row.get("LeaseCash", 0.0))

                    st.markdown(f"**Mileage: {mileage:,} / yr**")

                    selling_price = st.number_input(
                        f"Selling Price ($) — {term} mo / {mileage:,} mi",
                        value=msrp,
                        key=f"price_{term}_{mileage}"
                    )

                    with st.expander("Incentives"):
                        lease_cash_used = st.number_input(
                            f"Lease Cash Used ($) — Max: ${available_lease_cash:,.2f}",
                            min_value=0.0,
                            max_value=available_lease_cash,
                            value=0.0,
                            step=1.0,
                            key=f"lease_cash_{term}_{mileage}"
                        )

                    money_down_slider = st.slider(
                        f"Adjust Down Payment ($) — {term} mo / {mileage:,} mi",
                        min_value=0,
                        max_value=5000,
                        value=int(default_money_down),
                        step=50,
                        key=f"down_{term}_{mileage}"
                    )

                    K = 0.0
                    M = 250.0 + 650.0 + 62.50
                    Q = 0.0
                    τ = tax_rate
                    F = money_factor
                    W = term
                    SP = selling_price
                    RES = residual_value
                    U = 0.0


                    rebate_input = 0.0  # placeholder for future rebate support

                    # Step 1: Calculate deal charges using all funds
                    B_total = lease_cash_used + money_down_slider + rebate_input
                    TV_total = trade_value_input
                    _, _, debug_pre = calculate_ccr_full(
                        SP=SP,
                        B=B_total,
                        rebates=0.0,
                        TV=TV_total,

                   
                    )
                    initial_topval = debug_pre.get("Initial TopVal", 0.0)
                    deal_charges = max(0.0, -initial_topval)
                    st.markdown(f"**🔧 Deal Charges (Uncovered TopVal): ${deal_charges:,.2f}**")

                    used_for_deal = {
                        "lease_cash": 0.0,
                        "cash_down": 0.0,
                        "rebate": 0.0,
                        "trade": 0.0,
                    }

                    remaining_charges = deal_charges

                    # Deduct from lease cash, cash down, and rebates first
                    for key, amt in [
                        ("lease_cash", lease_cash_used),
                        ("cash_down", money_down_slider),
                        ("rebate", rebate_input),
                    ]:
                        used = min(amt, remaining_charges)
                        used_for_deal[key] = used
                        remaining_charges -= used

                    # Use trade value if charges remain
                    used_trade = min(trade_value_input, remaining_charges)
                    used_for_deal["trade"] = used_trade
                    remaining_charges -= used_trade

                    remaining = {
                        "lease_cash": lease_cash_used - used_for_deal["lease_cash"],
                        "cash_down": money_down_slider - used_for_deal["cash_down"],
                        "rebate": rebate_input - used_for_deal["rebate"],
                        "trade": trade_value_input - used_for_deal["trade"],
                    }

                    unpaid_balance = max(0.0, remaining_charges)

                    B = remaining["lease_cash"] + remaining["cash_down"] + remaining["rebate"]
                    TV_remaining = remaining["trade"]
                    S_final = SP - TV_remaining

                    st.markdown(f"**Adjusted B (CCR Cash Applied):** ${B:,.2f}")

                    ccr, overflow, debug_final = calculate_ccr_full(
                        SP=SP,
                        B=B,
                        rebates=0.0,
                        TV=TV_remaining,
                        K=K,
                        M=M,
                        Q=Q,
                        RES=RES,
                        F=F,
                        W=W,
                        τ=τ,
                        adjust_negative=False,
                    )

                    payment = calculate_payment_from_ccr(
                        S=S_final,
                        CCR=ccr,
                        RES=RES,
                        W=W,
                        F=F,
                        τ=τ,
                        M=M
                    )

                    st.markdown(f"**Monthly Payment: ${payment['Monthly Payment (MP)']:.2f}**")
                    st.markdown(f"*Base: ${payment['Base Payment (BP)']:.2f}, Tax: ${payment['Sales Tax (ST)']:.2f}, CCR: ${ccr:.2f}*")

                    if deal_charges > 0:
                        st.markdown(f"### 🔍 How Deal Charges Were Covered:")
                        st.markdown(f"- From Lease Cash: ${used_for_deal['lease_cash']:,.2f}")
                        st.markdown(f"- From Cash Down: ${used_for_deal['cash_down']:,.2f}")
                        st.markdown(f"- From Rebates: ${used_for_deal['rebate']:,.2f}")
                        st.markdown(f"- From Trade: ${used_for_deal['trade']:,.2f}")
                        if unpaid_balance > 0:
                            st.markdown(f"**Unpaid Balance:** ${unpaid_balance:,.2f}")

                    st.markdown(f"**Remaining Trade Applied to Price:** ${TV_remaining:.2f}")
                    st.markdown(f"**Remaining Cash Down Applied to CCR:** ${remaining['cash_down']:.2f}")
                    st.markdown(f"**Remaining Lease Cash Applied to CCR:** ${remaining['lease_cash']:.2f}")
                    st.markdown(f"**Remaining Rebates Applied to CCR:** ${remaining['rebate']:.2f}")

                    with st.expander("🔍 Debug Details"):
                        st.markdown("### Full CCR Debug Info")
                        st.json(debug_final)
                        st.markdown("### Payment Breakdown")
                        for k, v in payment.items():
                            if isinstance(v, (int, float)):
                                st.markdown(f"**{k}:** ${v:,.2f}")
                            else:
                                st.markdown(f"**{k}:** {v}")
