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
`setting_page.py`. Click the **Settings** button in the app to open this page.
The sidebar provides options to change values and a **Reset to Defaults** button
that restores the original configuration.
