from datetime import datetime
import os
import shutil
from pathlib import Path
from pypdf import PdfReader
import sys
from dotenv import load_dotenv
from urllib.parse import quote
from urllib.parse import quote
import webbrowser

load_dotenv()

def main() -> None:
    print("Invoicectl initialized, checking for today's latest invoice... ")

    # Check downloads folder for invoices
    home_dir = Path.home()
    downloads_dir = home_dir / "Downloads"

    print(f"Looking for invoices in: {downloads_dir}...")

    # Try to find the latest invoice in the downloads folder
    invoices = list(downloads_dir.glob("Invoice*.pdf"))
    latest_invoice : Path | None = None

    if invoices:
        latest_invoice = max(invoices, key=lambda f: f.stat().st_mtime)
        print(f"Latest invoice found: {latest_invoice}")

    if not latest_invoice:
        print("No invoices found... Exiting.")
        sys.exit(1)

    # Get invoice content
    reader = PdfReader(str(latest_invoice))
    invoice_page = reader.pages[0]
    invoice_text = invoice_page.extract_text()

    invoice_number = ""
    invoice_number_string_match = "Invoice Number:"
    period = ""
    period_string_match = "Period:"
    due_date = ""
    due_date_string_match = "Payment Due:"
    invoice_date = ""
    invoice_date_string_match = "Invoice Date:"

    # Extract variables from invoice content
    invoice_lines = invoice_text.splitlines()
    for line in invoice_lines:
        if invoice_number_string_match in line:
            invoice_number = line.split(invoice_number_string_match)[1].strip()
        elif period_string_match in line:
            period = line.split(period_string_match)[1].strip()
        elif due_date_string_match in line:
            string_date = line.split(due_date_string_match)[1].strip()
            due_date = convert_date(string_date)
        elif invoice_date_string_match in line:
            string_date = line.split(invoice_date_string_match)[1].strip()
            invoice_date = convert_date(string_date, "%Y%m%d")

    print(f"Invoice Number: {invoice_number}")
    print(f"Period: {period}")
    print(f"Payment Due: {due_date}")
    print(f"Invoice Date: {invoice_date}")

    input("Press Enter to use this invoice...")

    file_prefix = os.getenv("FILE_PREFIX", "")
    if not file_prefix:
        print("FILE_PREFIX not set in environment... Exiting.")
        sys.exit(1)

    new_file_name = f"{file_prefix}{invoice_date}.pdf"
    new_file_path = downloads_dir / new_file_name
    
    if not Path(new_file_path).exists():
        shutil.copy(latest_invoice, new_file_path)

    to = os.getenv("TO", "")
    subject = os.getenv("SUBJECT", "")
    body = os.getenv("BODY", "")

    if not to or not subject or not body:
        print("TO, SUBJECT, or BODY not set in environment... Exiting.")
        sys.exit(1)

    subject = subject.format(invoice_number=invoice_number, period=period, due_date=due_date)
    body = body.format(period=period)

    mailto = f"mailto:{to}?subject={quote(subject)}&body={quote(body)}"
    webbrowser.open(mailto)

def convert_date(string_date: str, format: str = "%m/%d/%y") -> str:
    date_obj = datetime.strptime(string_date, "%B %d, %Y")
    return date_obj.strftime(format)