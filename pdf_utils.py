import os
import logging
from datetime import datetime
from io import BytesIO


logger = logging.getLogger(__name__)
try:
    from weasyprint import HTML
    _WEASYPRINT_AVAILABLE = True
except Exception as exc:  # ImportError or OSError when native libs are missing
    _WEASYPRINT_AVAILABLE = False
    _WEASYPRINT_ERROR = exc
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
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
    if _WEASYPRINT_AVAILABLE:
        try:
            return HTML(string=html_content, base_url=os.getcwd()).write_pdf()
        except Exception as e:
            logger.error("Failed to generate PDF using WeasyPrint: %s", e)
            logger.debug(
                "------ BEGIN QUOTE HTML ------\n%s\n------ END QUOTE HTML ------",
                html_content,
            )
            raise RuntimeError("Failed to generate PDF") from e

    # Fallback implementation using ReportLab when WeasyPrint is unavailable
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("Lease Quote Summary", styles["Title"]),
        Paragraph(f"Customer: {customer_name}", styles["Normal"]),
        Paragraph(
            f"Vehicle: {year} {make} {model} {trim} | MSRP: ${msrp:,.2f} | VIN: {vin}",
            styles["Normal"],
        ),
        Paragraph(
            f"Dealership: Mathew's Hyundai | Date: {datetime.today().strftime('%B %d, %Y')}",
            styles["Normal"],
        ),
    ]

    header_row = ["Down Payment"] + [
        f"{opt['term']} Mo | {opt['mileage']:,} mi/yr" for opt in selected_options
    ]
    table_data = [header_row]

    for down_val in default_rows:
        row = [f"${down_val:,.2f} Down"]
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
            row.append(f"${payment:,.2f}/mo")
        table_data.append(row)

    table = Table(table_data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )

    elements.append(table)
    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(
            "Customer Signature: _______________________________ Date: ____________",
            styles["Normal"],
        )
    )
    elements.append(
        Paragraph(
            "Disclaimers: Estimates only. Subject to credit approval, taxes, fees, and final dealer terms. Contact for details.",
            styles["Normal"],
        )
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer
