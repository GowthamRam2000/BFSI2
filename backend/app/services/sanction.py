from __future__ import annotations

from datetime import datetime
from typing import Dict, Tuple

import hashlib
import hmac

from fpdf import FPDF

from app.config import get_settings


def generate_sanction_pdf(payload: Dict[str, str]) -> Tuple[bytes, str, str, str]:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Personal Loan Slip (Sanction Letter)", ln=True)

    pdf.set_font("Helvetica", size=11)
    pdf.ln(4)
    issued_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
    pdf.cell(0, 8, f"Date: {issued_at}", ln=True)
    pdf.ln(2)

    lines = [
        f"Customer Name: {payload.get('name', 'Customer')}",
        f"Customer ID: {payload.get('customer_id', 'N/A')}",
        f"Loan Amount: INR {payload.get('amount', 'N/A')}",
        f"Tenure: {payload.get('tenure_months', 'N/A')} months",
        f"Interest Rate: {payload.get('interest_rate', 'N/A')}% p.a.",
        f"Rate Tier: {payload.get('rate_tier', 'N/A')}",
        f"Estimated EMI: INR {payload.get('emi', 'N/A')}",
        f"Pre-approved Limit: INR {payload.get('pre_approved_limit', 'N/A')}",
        f"Insurance Add-on: {payload.get('insurance_opted', 'No')}",
    ]

    for line in lines:
        pdf.cell(0, 8, line, ln=True)

    signature, secure_ref = _sign_payload(payload, issued_at)
    pdf.ln(4)
    pdf.cell(0, 8, f"Secure Reference: {secure_ref}", ln=True)
    pdf.multi_cell(0, 8, f"Digital Signature (SHA-256): {signature}")

    pdf.ln(6)
    pdf.multi_cell(
        0,
        8,
        "This sanction letter is system-generated and subject to successful verification of the provided documents."
        " Please contact your relationship manager for any clarifications.",
    )

    pdf.ln(10)
    pdf.cell(0, 8, "Regards,", ln=True)
    pdf.cell(0, 8, "NBFC Digital Lending Team", ln=True)

    output = pdf.output(dest="S")
    if isinstance(output, bytearray):
        pdf_bytes = bytes(output)
    elif isinstance(output, bytes):
        pdf_bytes = output
    else:
        pdf_bytes = str(output).encode("latin-1")
    filename = f"loan_slip_{payload.get('customer_id', 'prospect')}_{int(datetime.utcnow().timestamp())}.pdf"
    return pdf_bytes, filename, signature, secure_ref


def _sign_payload(payload: Dict[str, str], issued_at: str) -> Tuple[str, str]:
    settings = get_settings()
    secret = settings.loan_signature_secret or "demo-secret"
    items = [f"{key}={payload.get(key, '')}" for key in sorted(payload.keys())]
    items.append(f"issued_at={issued_at}")
    message = "|".join(items).encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return digest, digest[:12].upper()
