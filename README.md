# Lease Quote Application

This repository contains a Streamlit application for calculating vehicle lease quotes.

## Running the app

Install the required packages from `requirements.txt` and launch Streamlit:

```bash
pip install -r requirements.txt
streamlit run lease_app.py
```

## Adjusting settings

Financial parameters are configured directly from the sidebar. Available options
include entering a trade‑in value, specifying customer cash down and toggling a
money factor markup. Sorting and filtering controls allow you to refine quote
options by term or mileage.

Each lease term and mileage combination provides an **Incentives** expander
for lease cash input (defaults to zero). A **Details** expander displays the
money factor, MSRP, residual value and payment formula components.

## Mobile Support

The app now uses a centered layout and includes responsive CSS rules. On narrow
screens, sidebars and quote cards stack vertically, allowing the tool to be used
comfortably on phones and tablets.
