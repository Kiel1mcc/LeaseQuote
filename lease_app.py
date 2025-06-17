# lease_app.py
import streamlit as st
import pandas as pd
from lease_calculations import calculate_base_and_monthly_payment as calculate_payment

@st.cache_data
def load_counties():
    """Load the CSV that contains each county's total sales-tax rate."""
    df = pd.read_csv("County_Tax_Rates.csv")
    # Expecting columns: "County" and "Total Local & State Sales Tax Rate"
    return df

@st.cache_data
def load_lease_programs():
    """Load the CSV that contains all lease programs / credit tiers."""
    df = pd.read_csv("All_Lease_Programs_Database.csv")
    # Expecting columns: "Credit_Tier", "Money_Factor", "Residual_Pct", "Term"
    return df

def show_quote_page():
    st.title("🔑 Lease Quote")

    # --- Inputs ---
    vin = st.text_input("Enter VIN or Stock #")

    msrp = st.number_input(
        "MSRP (Selling Price)", 
        min_value=0.0, step=100.0, value=0.0, format="%.2f"
    )
    money_down = st.number_input(
        "Down Payment", 
        min_value=0.0, step=100.0, value=0.0, format="%.2f"
    )
    rebate = st.number_input(
        "Rebate", 
        min_value=0.0, step=100.0, value=0.0, format="%.2f"
    )

    # County → look up tax rate
    df_counties = load_counties()
    county = st.selectbox("Select Tax County", df_counties["County"].tolist())
    tax_pct = (
        df_counties
        .loc[df_counties["County"] == county, "Total Local & State Sales Tax Rate"]
        .iat[0]
        / 100.0
    )

    # Credit‐tier → look up money factor & residual
    df_programs = load_lease_programs()
    tier = st.selectbox("Select Credit Tier", df_programs["Credit_Tier"].unique())
    tier_row = df_programs[df_programs["Credit_Tier"] == tier].iloc[0]
    money_factor = float(tier_row["Money_Factor"])
    residual_pct = float(tier_row["Residual_Pct"])  # e.g. 0.60 for 60%

    # Term & mileage
    term = st.selectbox(
        "Term (months)", 
        sorted(df_programs["Term"].unique().astype(int).tolist())
    )
    mileage = st.selectbox(
        "Annual Mileage", 
        ["10,000", "12,000", "15,000"]
    )

    # (Optional) credit‐score slider if you use it in your logic
    credit_score = st.slider(
        "Estimated Credit Score", 
        min_value=300, max_value=850, value=700
    )

    # --- Calculate & Output ---
    if st.button("Calculate"):
        base_pay, monthly_pay = calculate_payment(
            msrp=msrp,
            money_factor=money_factor,
            term=int(term),
            residual_pct=residual_pct,
            tax_rate=tax_pct,
            down_payment=money_down,
            rebate=rebate,
        )

        st.success("✅ Calculation complete!")
        col1, col2 = st.columns(2)
        col1.metric("Base Payment", f"${base_pay:,.2f}")
        col2.metric("Monthly Payment", f"${monthly_pay:,.2f}")

def main():
    show_quote_page()

if __name__ == "__main__":
    main()
