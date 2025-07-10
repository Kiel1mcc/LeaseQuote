from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from utils import calculate_option_payment


def generate_quote_pdf(selected_options, tax_rate, base_down, customer_name, vehicle_info):
    """Return a PDF bytes object summarizing lease options."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    year = vehicle_info.get("year", "N/A")
    make = vehicle_info.get("make", "N/A")
    model = vehicle_info.get("model", "N/A")
    trim = vehicle_info.get("trim", "N/A")
    msrp = vehicle_info.get("msrp", 0.0)
    vin = vehicle_info.get("vin", "N/A")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 1 * inch, "Lease Quote Summary")
    c.setFont("Helvetica", 10)
    c.drawString(1 * inch, height - 1.3 * inch, f"Customer: {customer_name}")
    c.drawString(
        1 * inch,
        height - 1.5 * inch,
        f"Vehicle: {year} {make} {model} {trim} | MSRP: ${msrp:,.2f} | VIN: {vin}",
    )
    c.drawString(
        1 * inch,
        height - 1.7 * inch,
        f"Dealership: Mathew's Hyundai | Date: {datetime.today().strftime('%B %d, %Y')}",
    )

    y = height - 2.2 * inch
    default_rows = [base_down + 1500 * i for i in range(3)]
    col_widths = [1.5 * inch] + [2 * inch] * len(selected_options)

    c.drawString(1 * inch, y, "Down Payment")
    for i, opt in enumerate(selected_options):
        c.drawCentredString(
            1 * inch + col_widths[0] + i * col_widths[1] + col_widths[1] / 2,
            y,
            f"{opt['term']} Mo | {opt['mileage']:,} mi/yr",
        )
    y -= 0.3 * inch

    for default_val in default_rows:
        down_val = default_val
        c.drawString(1 * inch, y, f"${down_val:,.2f}")
        for i, opt in enumerate(selected_options):
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
            payment = payment_data["payment"]
            c.drawRightString(
                1 * inch + col_widths[0] + (i + 1) * col_widths[1] - 0.1 * inch,
                y,
                f"${payment:,.2f}/mo",
            )
        y -= 0.3 * inch

    y -= 0.5 * inch
    for opt in selected_options:
        payment_data = calculate_option_payment(
            opt['selling_price'],
            opt['lease_cash_used'],
            opt['residual_value'],
            opt['money_factor'],
            opt['term'],
            0.0,
            base_down,
            tax_rate,
        )
        payment = payment_data["payment"]
        c.drawString(
            1 * inch,
            y,
            f"\u2610 ${base_down:,.2f} Down \u2014 {opt['term']} Mo | {opt['mileage']:,} mi/yr \u2014 ${payment:,.2f}/mo",
        )
        y -= 0.25 * inch

    y -= 0.5 * inch
    c.drawString(
        1 * inch, y, "Customer Signature: _______________________________ Date: _______________"
    )

    y -= 0.5 * inch
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(
        1 * inch,
        y,
        "Disclaimers: Estimates only. Subject to credit approval, taxes, fees, and final dealer terms. Contact for details.",
    )

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
