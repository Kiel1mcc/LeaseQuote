# lease_app.py
import streamlit as st
import pandas as pd
from lease_calculations import calculate_base_and_monthly_payment
from setting_page import show_settings

st.set_page_config(page_title="Lease Quote Tool")

# --- Session state for page navigation ---
if 'page' not in st.session_state:
    st.session_state.page = 'main'

# --- Data loading (from GitHub raw URLs) ---
@st.cache_data
def load_data():
    base_url = (
        'https://raw.githubusercontent.com/<your-username>/<your-repo>/main/data'
    )
    lease_programs = pd.read_csv(f"{base_url}/All_Lease_Programs_Database.csv")
    inventory = pd.read_excel(f"{base_url}/Locator_Detail_20250605.xlsx")
    county_rates = pd.read_csv(f"{base_url}/County_Tax_Rates.csv")
    return lease_programs, inventory, county_rates

lease_programs, inventory, county_rates = load_data()

# --- Settings Page ---
if st.session_state.page == 'settings':
    show_settings()
    if st.button('Return to Quote'):
        st.session_state.page = 'main'

# --- Main Quote Page ---
else:
    st.title('📑 Lease Quote Tool')
    
    # Inputs
    col1, col2 = st.columns(2)
    vin_input = col1.text_input('VIN or Stock Number')
    default_county = st.session_state.get('default_county', None)
    county = col2.selectbox(
        'County',
        options=sorted(county_rates['County']),
        index=(sorted(county_rates['County']).index(default_county)
               if default_county in county_rates['County'].tolist() else 0)
    )

    # Lookup vehicle
    vehicle = inventory[
        (inventory['VIN'].astype(str) == str(vin_input)) |
        (inventory['Stock No.'].astype(str) == str(vin_input))
    ]

    if not vin_input:
        st.info('Enter a VIN or Stock number above.')
    elif vehicle.empty:
        st.error('Vehicle not found.')
    else:
        msrp = float(vehicle['MSRP'].iloc[0])
        st.write(f"**MSRP:** ${msrp:,.0f}")
        rebate = float(vehicle.get('Rebate', 0).iloc[0])
        apply_rebate = st.checkbox(f"Apply Rebate (${rebate:,.0f})", value=True)
        money_down = st.number_input('Money Down', min_value=0, value=0, step=500)
        
        # Lease program selectors
        term = st.selectbox(
            'Term (months)',
            options=sorted(lease_programs['Term (mo)'].unique())
        )
        mileage = st.selectbox(
            'Mileage (miles/year)',
            options=sorted(lease_programs['Miles'].unique())
        )
        tiers = st.session_state.get('tiers', ['Tier 1', 'Tier 2', 'Tier 3'])
        tier = st.selectbox('Credit Tier', options=tiers)
        
        if st.button('Calculate Payment'):
            tax_rate = (
                float(
                    county_rates.loc[
                        county_rates['County'] == county, 'Total State & Local Tax Rate'
                    ].iloc[0].replace('%','')
                ) / 100
            )
            result = calculate_base_and_monthly_payment(
                msrp=msrp,
                mileage=mileage,
                term=term,
                tax_rate=tax_rate,
                money_down=money_down,
                rebate=(rebate if apply_rebate else 0),
                lease_programs=lease_programs,
                tier=tier
            )
            st.subheader('🔍 Calculation Results')
            st.write(result)

        if st.button('⚙️ Settings'):
            st.session_state.page = 'settings'

# setting_page.py
import streamlit as st

def show_settings():
    st.header('⚙️ Settings')
    
    # Default County
    county_list = st.session_state.get('county_list', [])
    default = st.selectbox(
        'Default County',
        options=sorted(st.session_state.get('county_list', [])),
        index=0
    )
    st.session_state.default_county = default
    
    # Credit Tiers
    tiers = st.text_area(
        'Credit Tiers (one per line)',
        value='\n'.join(st.session_state.get('tiers', ['Tier 1','Tier 2','Tier 3']))
    )
    st.session_state.tiers = [t.strip() for t in tiers.split('\n') if t.strip()]

# lease_calculations.py
def calculate_base_and_monthly_payment(
    msrp, mileage, term, tax_rate,
    money_down, rebate, lease_programs, tier
):
    # Filter for the appropriate lease program
    program = lease_programs[
        (lease_programs['Term (mo)'] == term) &
        (lease_programs['Miles'] == mileage)
    ].iloc[0]
    mf = float(program['Money Factor'])
    rv = float(program['Residual'])

    # Mileage adjustment for 10k leases (33-48 mo)
    if mileage == 10000 and 33 <= term <= 48:
        rv += 0.01

    net_cap_cost = msrp - money_down - rebate
    resid_val = msrp * rv
    depreciation = net_cap_cost - resid_val
    base_payment = (depreciation / term) + (net_cap_cost + resid_val) * mf
    tax_amount = base_payment * tax_rate
    total_monthly = base_payment + tax_amount

    return {
        'money_factor': round(mf, 5),
        'residual_percent': round(rv, 4),
        'residual_value': round(resid_val, 2),
        'base_monthly': round(base_payment, 2),
        'tax_per_month': round(tax_amount, 2),
        'total_monthly_payment': round(total_monthly, 2)
    }
