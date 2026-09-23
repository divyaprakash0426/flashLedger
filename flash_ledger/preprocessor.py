"""Financial statement preprocessor and bank feed cleaner."""

from __future__ import annotations
import csv
import datetime
import re
import uuid
from pathlib import Path
from typing import Any
from flash_ledger.models import Transaction

# Common payment aggregator and POS terminal prefixes to strip
NOISY_PREFIXES = [
    r"^SQ\s*\*\s*",                     # Square
    r"^TST\s*\*\s*",                    # Toast POS
    r"^PAYPAL\s*\*\s*",                 # PayPal
    r"^GITHUB\s*\*\s*",                 # GitHub
    r"^DRI\s*\*\s*",                    # Digital River
    r"^SP\s*\*\s*",                     # Shopify
    r"^UBER\s*\*\s*",                   # Uber
    r"^LYFT\s*\*\s*",                   # Lyft
    r"^FS\s*\*\s*",                     # FastSpring
    r"^CHECKCARD\s+\d{4}\s+",
    r"^POS\s+DEBIT\s+",
    r"^PURCHASE\s+AUTHORIZED\s+ON\s+\d{2}/\d{2}\s+",
    r"^DEBIT\s+CARD\s+PURCHASE\s+",
    r"^VND\s*\*\s*",
]

# US State abbreviations commonly found at the end of bank strings
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
}


def clean_merchant_string(raw: str) -> str:
    """Strips terminal noise, POS codes, phone numbers, and location codes from raw bank strings."""
    if not raw:
        return ""

    s = raw.strip()

    # Step 1: Special case Amazon strings before prefix stripping
    if re.match(r"^AMZN\b|^AMAZON\b", s, flags=re.IGNORECASE):
        # Check if there is a subcategory like Prime, Web Services, etc.
        if re.search(r"Prime", s, flags=re.IGNORECASE):
            return "Amazon Prime"
        if re.search(r"AWS|Web\s*Services", s, flags=re.IGNORECASE):
            return "Amazon Web Services (AWS)"
        return "Amazon"

    # Step 2: Strip noisy merchant prefixes
    for prefix in NOISY_PREFIXES:
        if prefix.startswith(r"^GITHUB") and re.match(prefix, s, flags=re.IGNORECASE):
            s = "GitHub " + re.sub(prefix, "", s, flags=re.IGNORECASE)
            break
        elif prefix.startswith(r"^UBER") and re.match(prefix, s, flags=re.IGNORECASE):
            s = "Uber " + re.sub(prefix, "", s, flags=re.IGNORECASE)
            break
        else:
            s = re.sub(prefix, "", s, flags=re.IGNORECASE)

    # Step 3: Strip phone numbers like 800-692-7753, 877-448, 408-555-0199
    s = re.sub(r"\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b", "", s)
    s = re.sub(r"\b\d{3}-\d{3,4}\b", "", s)

    # Step 4: Strip trailing store/terminal numbers like #104, STORE 3912, *284J1
    s = re.sub(r"#\s*\d+", "", s)
    s = re.sub(r"\*[\w\d]+", "", s)
    s = re.sub(r"\bSTORE\s*\d+\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\bLOC(?:ATION)?\s*\d+\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\b\d{4,}\b", "", s)  # long numeric codes

    # Step 5: Strip specific noise keywords
    s = re.sub(r"\bSUBSCRIPTION\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\bPENDING\b", "", s, flags=re.IGNORECASE)

    # Step 6: Clean whitespace and trailing punctuation
    s = re.sub(r"[\*#\-_]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # Step 7: Strip trailing state abbreviation if preceded by city/location
    tokens = s.split()
    if len(tokens) >= 2 and tokens[-1].upper() in US_STATES:
        tokens.pop()
        # If city name was also trailing like 'San Francisco', keep or refine
        s = " ".join(tokens)

    # Step 8: Title case if all upper or all lower
    if s.isupper() or s.islower():
        words = []
        for word in s.split():
            if word.upper() in {"LLC", "INC", "LTD", "CORP", "CO", "US", "UK", "AWS", "GCP", "AI"}:
                words.append(word.upper())
            else:
                words.append(word.capitalize())
        s = " ".join(words)

    return s.strip()


def parse_amount(val: str | float | int) -> float:
    """Parse string/float amount into a clean float (handles $, £, €, commas, parenthesized negatives)."""
    if isinstance(val, (int, float)):
        return float(val)

    if not isinstance(val, str):
        return 0.0

    s = val.strip()
    if not s:
        return 0.0

    # Handle parenthesized negative: (15.50) -> -15.50
    is_negative = False
    if s.startswith("(") and s.endswith(")"):
        is_negative = True
        s = s[1:-1].strip()

    # Strip currency symbols and commas
    s = re.sub(r"[$£€₹,\s]", "", s)

    # Check for leading negative sign
    if s.startswith("-"):
        is_negative = True
        s = s[1:].strip()
    elif s.startswith("+"):
        s = s[1:].strip()

    try:
        num = float(s)
        return -num if is_negative else num
    except ValueError:
        return 0.0


def parse_statement_csv(filepath: str | Path) -> list[Transaction]:
    """Parse CSV statements from Chase, Amex, Brex, Mercury, UK Gov, or generic formats."""
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"Statement file not found: {p}")

    transactions: list[Transaction] = []

    with open(p, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        field_map = {fn.strip().lower(): fn for fn in fieldnames}

        # Check if this is UK Gov format with Supplier + Description
        supplier_col = field_map.get("supplier") or field_map.get("payee") or field_map.get("merchant name")
        desc_col = (
            field_map.get("description")
            or field_map.get("narrative")
            or field_map.get("transaction_description")
            or field_map.get("details")
        )

        # Date column
        date_col = (
            field_map.get("posting date")
            or field_map.get("date")
            or field_map.get("transaction date")
            or field_map.get("post date")
        )

        # Amount column
        amount_col = (
            field_map.get("amount")
            or field_map.get("total")
            or field_map.get("gross amount")
            or field_map.get("net")
            or field_map.get("amount (gbp)")
        )

        currency_col = field_map.get("currency")
        default_currency = "GBP" if "department family" in field_map or "expense area" in field_map else "USD"

        if not desc_col and not supplier_col:
            raise ValueError(f"Could not identify transaction description column in {p}. Available: {fieldnames}")

        row_idx = 0
        for row in reader:
            row_idx += 1
            supplier_val = row.get(supplier_col, "").strip() if supplier_col else ""
            desc_val = row.get(desc_col, "").strip() if desc_col else ""

            # Combine supplier and description if both exist and differ
            if supplier_val and desc_val and supplier_val.lower() not in desc_val.lower():
                raw_desc = f"{supplier_val} - {desc_val}"
            elif supplier_val:
                raw_desc = supplier_val
            else:
                raw_desc = desc_val

            if not raw_desc:
                continue

            # Amount
            amt_val = row.get(amount_col, 0.0) if amount_col else 0.0
            amount = parse_amount(amt_val)

            # Date
            date_val = row.get(date_col, "") if date_col else ""
            parsed_date = _parse_date(date_val)

            # Currency
            curr = row.get(currency_col, default_currency) if currency_col else default_currency
            if not curr:
                curr = default_currency

            clean_desc = clean_merchant_string(raw_desc)
            txn_id = f"txn_{row_idx:05d}_{uuid.uuid4().hex[:6]}"

            transactions.append(
                Transaction(
                    id=txn_id,
                    date=parsed_date,
                    raw_description=raw_desc,
                    clean_description=clean_desc,
                    amount=amount,
                    currency=curr,
                    account=row.get("Account", "Statement Account") or "Statement Account",
                )
            )

    return transactions


def _parse_date(val: str) -> datetime.date:
    """Helper to parse common date formats."""
    if not val:
        return datetime.date.today()

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%m/%d/%y",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(val.strip(), fmt).date()
        except ValueError:
            pass
    return datetime.date.today()
