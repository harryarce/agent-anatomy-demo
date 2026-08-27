from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def write_policy(data_dir: Path) -> None:
    text = """Contoso Returns and Refund Policy

Section 3.1: Standard refunds require proof of purchase and delivery timeline.
Section 4.2: Orders delivered more than 7 days late are eligible for a shipping refund and up to 25 percent item refund after verification.
Section 6.1: Refund decisions must include policy citation and order evidence.
"""
    (data_dir / "refund-policy.txt").write_text(text, encoding="utf-8")

    # Minimal PDF payload written with stdlib only for deterministic local demos.
    pdf_bytes = (
        b"%PDF-1.1\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 122>>stream\n"
        b"BT /F1 12 Tf 72 720 Td (Section 4.2: Orders delivered more than 7 days late are eligible for refund review.) Tj ET\n"
        b"endstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n0\n%%EOF\n"
    )
    (data_dir / "refund-policy.pdf").write_bytes(pdf_bytes)


def write_orders_db(data_dir: Path) -> None:
    db = data_dir / "orders.db"
    if db.exists():
        db.unlink()
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TABLE orders (order_id INTEGER PRIMARY KEY, customer TEXT, days_late INTEGER, status TEXT, carrier TEXT)"
        )
        conn.execute(
            "INSERT INTO orders (order_id, customer, days_late, status, carrier) VALUES (4471, 'Contoso', 9, 'delivered', 'Northwind Freight')"
        )
        conn.execute(
            "INSERT INTO orders (order_id, customer, days_late, status, carrier) VALUES (5022, 'Fabrikam', 0, 'delivered', 'Litware Logistics')"
        )
        conn.commit()


def write_crm(data_dir: Path) -> None:
    payload = [
        {"id": "cust-contoso", "name": "Contoso", "tier": "enterprise", "region": "NA"},
        {"id": "cust-tailspin", "name": "Tailspin Toys", "tier": "standard", "region": "EU"},
    ]
    (data_dir / "crm.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_tickets(data_dir: Path) -> None:
    tickets_dir = data_dir / "tickets"
    tickets_dir.mkdir(parents=True, exist_ok=True)
    failures = [
        {"id": "T-100", "error": "approved without policy citation"},
        {"id": "T-101", "error": "wrong customer in response body"},
        {"id": "T-102", "error": "ignored shipping delay threshold"},
        {"id": "T-103", "error": "no order lookup before recommendation"},
    ]
    (tickets_dir / "failures.json").write_text(json.dumps(failures, indent=2), encoding="utf-8")


def write_instruction_variants(data_dir: Path) -> None:
    instructions = data_dir / "instructions"
    instructions.mkdir(parents=True, exist_ok=True)
    (instructions / "terse_expert.txt").write_text("Be concise, cite policy, and avoid unsupported claims.", encoding="utf-8")
    (instructions / "patient_teacher.txt").write_text(
        "Explain each verification step and show where evidence is missing.",
        encoding="utf-8",
    )
    (instructions / "hostile_reviewer.txt").write_text(
        "Challenge every unsupported statement and demand citations.",
        encoding="utf-8",
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    write_policy(data_dir)
    write_orders_db(data_dir)
    write_crm(data_dir)
    write_tickets(data_dir)
    write_instruction_variants(data_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())