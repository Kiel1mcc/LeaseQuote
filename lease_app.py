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
    trade_value = st.number_input("Trade Value ($)", min_value=0.0, value=0.0, step=100.0)
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

                    cash_down = default_money_down
                    initial_B = lease_cash_used

                    # Run CCR with lease cash only
                    ccr, overflow, debug_ccr = calculate_ccr_full(
                        SP=selling_price,
                        B=initial_B,
                        rebates=0.0,
                        TV=0.0,
                        K=0.0,
                        M=962.50,
                        Q=0.0,
                        RES=residual_value,
                        F=money_factor,
                        W=term,
                        τ=tax_rate
                    )

                    # Fill overflow: trade first, then cash
                    trade_used = min(trade_value, overflow)
                    remaining_gap = overflow - trade_used
                    cash_used = min(cash_down, remaining_gap)

                    remaining_trade = trade_value - trade_used
                    remaining_cash = cash_down - cash_used

                    adjusted_SP = selling_price  # don't apply trade reduction yet
                    total_B = initial_B + trade_used + cash_used + remaining_cash

                    # Recalculate CCR with updated values
                    ccr, _, debug_ccr = calculate_ccr_full(
                        SP=adjusted_SP,
                        B=total_B,
                        rebates=0.0,
                        TV=0.0,
                        K=0.0,
                        M=962.50,
                        Q=0.0,
                        RES=residual_value,
                        F=money_factor,
                        W=term,
                        τ=tax_rate
                    )

                    adjusted_SP -= remaining_trade  # now reduce SP only after CCR is handled

                    payment = calculate_payment_from_ccr(
                        S=adjusted_SP,
                        CCR=ccr,
                        RES=residual_value,
                        W=term,
                        F=money_factor,
                        τ=tax_rate,
                        M=962.50,
                        Q=0.0
                    )

                    st.markdown(f"**Monthly Payment: ${payment['Monthly Payment (MP)']:.2f}**")
                    st.markdown(
                        f"*Base: ${payment['Base Payment (BP)']:.2f}, Tax: ${payment['Sales Tax (ST)']:.2f}, "
                        f"CCR: ${ccr:.2f}, Trade Used: ${trade_used:.2f}, Remaining Cash Added to Down: ${remaining_cash:.2f}*"
                    )

                    with st.expander("🔍 Full Debug Info"):
                        st.markdown("### CCR Fill Breakdown")
                        st.json({
                            "TopVal Overflow": round(overflow, 2),
                            "Trade Used for Overflow": trade_used,
                            "Cash Used for Overflow": cash_used,
                            "Remaining Trade (Reduced SP)": remaining_trade,
                            "Remaining Cash (Added to Down)": remaining_cash,
                            "Final SP": adjusted_SP,
                            "Final B": total_B
                        })

                        st.markdown("### CCR Debug")
                        st.json(debug_ccr)

                        st.markdown("### Final Payment Breakdown")
                        st.json(payment)
