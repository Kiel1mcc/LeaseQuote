# Lease Quote Application

This repository contains a Streamlit application for calculating vehicle lease quotes.

## Running the app

Install the required packages from `requirements.txt` and launch Streamlit:

```bash
pip install -r requirements.txt
streamlit run lease_app.py
```

## Adjusting settings

Application settings such as default tax county and tier are managed in
`setting_page.py`. Use the sidebar **Navigation** radio to switch to the
**Settings** page.
The sidebar provides options to change values and a **Reset to Defaults** button
that restores the original configuration. Global controls include:

- **Default Down Payment**: starting down payment value for each quote.
- **Apply Money Factor Markup**: toggles a 0.0004 increase to all money factors.
- **Sale Price**: adjust the selling price when reviewing lease programs.

Each lease term/mileage combination offers an **Incentives** expander where you
can enter the amount of lease cash to apply (defaults to zero). A **Details**
expander displays the money factor, MSRP, residual value, and payment formula
components.
