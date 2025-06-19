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

                    money_down_slider = st.slider(
                        f"Adjust Down Payment ($) — {term} mo / {mileage:,} mi",
                        min_value=0,
                        max_value=5000,
                        value=int(default_money_down),
                        step=50,
                        key=f"down_{term}_{mileage}"
                    )

                    B = money_down_slider + lease_cash_used
                    K = 0.0
                    U = 0.0
                    M = 250.0 + 650.0 + 62.50
                    Q = 0.0
                    τ = tax_rate
                    F = money_factor
                    W = term
                    TV = trade_value
                    SP = selling_price
                    RES = residual_value
                    S = selling_price

                    ccr, overflow = calculate_ccr_full(
                        SP=SP,
                        B=B,
                        rebates=0.0,
                        TV=TV,
                        K=K,
                        M=M,
                        Q=Q,
                        RES=RES,
                        F=F,
                        W=W,
                        τ=τ
                    )

                    # Show intermediate values
                    bottomVal = (1 + τ) * (1 - (F + 1 / W)) - τ * F * (1 + F * W)
                    topVal = B - K - (
                        F * (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U + RES) +
                        (S + M + Q + τ * (F * W * (S + M - U + RES) + (S + M - U - RES)) - U - RES) / W
                    )
                    st.markdown(f"**Top Value (Numerator for CCR):** {topVal:.6f}")
                    st.markdown(f"**Bottom Value (Denominator for CCR):** {bottomVal:.6f}")

                    payment = calculate_payment_from_ccr(
                        SP=SP,
                        CCR=ccr,
                        RES=RES,
                        W=W,
                        F=F,
                        τ=τ
                    )

                    st.markdown(f"**Money Factor:** {F:.6f}  ")
                    st.markdown(f"**MSRP:** ${msrp:,.2f}  ")
                    st.markdown(f"**Residual Value:** ${RES:,.2f}  ")
                    st.markdown(f"**Numerator:** {payment['Numerator (N)']:.6f}  ")
                    st.markdown(f"**Denominator:** {payment['Denominator (D)']}  ")
                    st.markdown(f"**Monthly Payment: ${payment['Monthly Payment (MP)']:.2f}**")
                    st.markdown(f"*Base: ${payment['Base Payment (BP)']:.2f}, Tax: ${payment['Sales Tax (ST)']:.2f}, CCR: ${ccr:.2f}*")

                    st.markdown("---")
                    st.markdown(f"**Variables Used:**  ")
                    st.markdown(f"B (Money Down + Lease Cash): ${B:,.2f}  ")
                    st.markdown(f"K (Inception Fees): ${K:,.2f}  ")
                    st.markdown(f"U (Unused Cap Reduction): ${U:,.2f}  ")
                    st.markdown(f"M (DOC + ACQ Fees): ${M:,.2f}  ")
                    st.markdown(f"Q (License + Title): ${Q:,.2f}  ")
                    st.markdown(f"τ (Tax Rate): {tax_rate:.4f}  ")
                    st.markdown(f"F (Money Factor): {F:.6f}  ")
                    st.markdown(f"W (Term): {W}  ")
                    st.markdown(f"TV (Trade Value): ${TV:,.2f}  ")
                    st.markdown(f"SP (Selling Price): ${SP:,.2f}  ")
                    st.markdown(f"S (Selling Price, duplicate): ${S:,.2f}  ")
                    st.markdown(f"RES (Residual): ${RES:,.2f}  ")
