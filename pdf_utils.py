import os
from datetime import datetime
import pdfkit
from utils import calculate_option_payment


def generate_quote_pdf(selected_options, tax_rate, base_down, customer_name, vehicle_info):
    """Generate a PDF from an HTML representation of the quote."""
    year = vehicle_info.get("year", "N/A")
    make = vehicle_info.get("make", "N/A")
    model = vehicle_info.get("model", "N/A")
    trim = vehicle_info.get("trim", "N/A")
    msrp = vehicle_info.get("msrp", 0.0)
    vin = vehicle_info.get("vin", "N/A")

    header_html = "<table class='lease-table'><tr><th>Down Payment</th>"
    for opt in selected_options:
        header_html += f"<th>{opt['term']} Mo | {opt['mileage']:,} mi/yr</th>"
    header_html += "</tr>"

    body_html = ""
    default_rows = [base_down + 1500 * i for i in range(3)]
    for down_val in default_rows:
        body_html += "<tr>"
        body_html += f"<td><strong>${down_val:,.2f} Down</strong></td>"
        for opt in selected_options:
            payment_data = calculate_option_payment(
                opt['selling_price'],
                opt['lease_cash_used'],
                opt['residual_value'],
                opt['money_factor'],
                opt['term'],
                0.0,
                down_val,
                tax_rate,
            )
            payment = payment_data['payment']
            body_html += f"<td class=\"checkbox-cell\">${payment:,.2f}/mo</td>"
        body_html += "</tr>"

    footer_html = "</table>"

    html_content = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <style>
        body, table, th, td {{
            font-family: Arial, sans-serif;
            font-size: 15px;
        }}
        table.lease-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}
        .lease-table th {{
            text-align: left;
            background-color: #f5f5f5;
            font-weight: 600;
            padding: 10px;
            border-bottom: 1px solid #ccc;
        }}
        .lease-table td {{
            padding: 10px;
            vertical-align: middle;
        }}
        .checkbox-cell::before {{
            content: '☐ ';
            font-size: 16px;
            margin-right: 4px;
            vertical-align: middle;
        }}
        </style>
    </head>
    <body>
        <h2>Lease Quote Summary</h2>
        <p>Customer: {customer_name}</p>
        <p>Vehicle: {year} {make} {model} {trim} | MSRP: ${msrp:,.2f} | VIN: {vin}</p>
        <p>Dealership: Mathew's Hyundai | Date: {datetime.today().strftime('%B %d, %Y')}</p>
        {header_html + body_html + footer_html}
        <p>Customer Signature: _______________________________ Date: _______________</p>
        <p style='font-size:12px;'>Disclaimers: Estimates only. Subject to credit approval, taxes, fees, and final dealer terms. Contact for details.</p>
    </body>
    </html>
    """

    config = pdfkit.configuration(wkhtmltopdf=os.getenv("WKHTMLTOPDF_BINARY", "/usr/bin/wkhtmltopdf"))
    return pdfkit.from_string(html_content, False, configuration=config, options={"enable-local-file-access": ""})
