# Lease Quote Application

This repository contains a Streamlit application for calculating vehicle lease quotes.

## Running the app

Install the required packages from `requirements.txt` and launch Streamlit:

```bash
pip install -r requirements.txt
streamlit run lease_app.py
```

### System packages for PDF generation

`pdf_utils.py` uses [WeasyPrint](https://weasyprint.org/) to produce PDF
documents. The Python package is already listed in `requirements.txt`, so make
sure you've installed all dependencies:

```bash
pip install -r requirements.txt
```

WeasyPrint also requires native libraries like cairo and pango. Install these
on Debian/Ubuntu systems:

```bash
sudo apt-get update
sudo apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info
```

On other Linux distributions, install the equivalent packages using your
system's package manager. After installing the native libraries you can
confirm WeasyPrint is working by running:

```bash
python -c "from weasyprint import HTML; print('WeasyPrint loaded')"
```

If you open the project in the included **devcontainer**, these packages are
installed automatically when the container is created.

Do **not** run the file directly with `python lease_app.py`. Session state and
other features only work when launching the app through the `streamlit` command.

## Adjusting settings

Financial parameters are configured directly from the sidebar. Available options
include entering a trade‑in value, specifying customer cash down and toggling a
money factor markup. Sorting and filtering controls allow you to refine quote
options by term or mileage.

Each lease term and mileage combination provides an **Incentives** expander
for lease cash input (defaults to zero). A **Details** expander displays the
money factor, MSRP, residual value and payment formula components.

## Mobile Support

The app now uses a wide layout and includes responsive CSS rules. On narrow
screens, sidebars and quote cards stack vertically, allowing the tool to be used
comfortably on phones and tablets.

**Tip:** If you want to use the VIN scanning feature on a phone or tablet, be
sure to access the app over **HTTPS**. Most browsers require a secure context to
allow camera access.
## VIN Scanner App

A standalone Streamlit app (`app.py`) lets you scan a Vehicle Identification Number using your phone camera. It supports barcode scanning with `pyzbar` and OCR via `easyocr`. If `streamlit-camera-input-live` is installed, you can also enable continuous scanning.

Install the extra packages and run the app:

```bash
pip install streamlit pyzbar pillow easyocr streamlit-camera-input-live
streamlit run app.py
```

When running on mobile, ensure the page loads over **HTTPS** and grant camera permissions. Tap the camera icon to switch to the back camera when available.

