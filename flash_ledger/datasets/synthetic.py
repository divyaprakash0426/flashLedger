"""Synthetic benchmark generator for realistic, noisy bank and corporate card feeds."""

from __future__ import annotations
import csv
import datetime
import random
import uuid
from pathlib import Path
from flash_ledger.models import Transaction
from flash_ledger.preprocessor import clean_merchant_string

MERCHANT_POOLS = [
    # (Category, Raw templates, amount_min, amount_max, weight)
    (
        "SaaS",
        [
            "GITHUB*SPONSOR {phone}",
            "AWS EMEA #{num5}",
            "AWS CLOUD SERVICES #{num6}",
            "AMZN Mktp US*{code5}",
            "SLACK TECHNOLOGIES INC {phone}",
            "NOTION LABS INC #{num4}",
            "DRI*OPENAI LLC *SUBSCRIPTION",
            "VERCEL INC SUB_{num6}",
            "DATADOG SAAS #{num5}",
            "FIGMA INC *TEAM PLAN",
            "GOOGLE*CLOUD #{num8}",
            "JETBRAINS S.R.O. #{num6}",
            "DOCKER INC #{num5}",
            "ZOOM.US 888-799-9666",
            "HUBSPOT INC #{num6}",
        ],
        12.00,
        1450.00,
        40,
    ),
    (
        "Meals",
        [
            "SQ *BLUE BOTTLE SOMA",
            "SQ *RITUAL COFFEE ROASTERS",
            "TST* TARTINE BAKERY #{num3}",
            "TST* PHILZ COFFEE #{num3}",
            "STARBUCKS STORE {num5} {state}",
            "CHIPOTLE ONLINE #{num4}",
            "SWEETGREEN #{num3} {state}",
            "UBER *EATS PENDING {city} {state}",
            "DOORDASH*RESTAURANT {num4}",
            "CAVIAR*DELIVERY #{num5}",
            "THE GRILLED CHEESE GRILL #{num3}",
        ],
        4.50,
        98.00,
        25,
    ),
    (
        "Travel & Transport",
        [
            "UBER *TRIP {num5} {city} {state}",
            "LYFT *RIDE {num5}",
            "UNITED AIRLINES {num8}",
            "DELTA AIR 006{num6}",
            "AIRBNB *HM{num6}",
            "MARRIOTT HOTEL #{num4} {city}",
            "FASTRAK TOLL #{num6}",
            "CALTRAIN TICKET #{num5}",
        ],
        14.00,
        1150.00,
        12,
    ),
    (
        "Office Supplies",
        [
            "AMAZON.COM*{num6} US",
            "STAPLES STORE #{num3}",
            "TARGET T-{num4} {state}",
            "OFFICE DEPOT #{num3}",
            "HOME DEPOT #{num4}",
        ],
        15.00,
        380.00,
        8,
    ),
    (
        "CapEx Hardware",
        [
            "APPLE STORE #{num3} {phone} {state}",
            "DELL DIRECT #{num6}",
            "LENOVO ONLINE STORE #{num5}",
            "B&H PHOTO VIDEO #{num6}",
            "BEST BUY #{num4} {state}",
        ],
        2600.00,
        5900.00,
        5,
    ),
    (
        "Professional Fees",
        [
            "COOLEY LLP LEGAL SERVICES #{num5}",
            "GUSTO PAYROLL SERVICES",
            "CARTA VALUATION SERVICES #{num4}",
            "DELOITTE TAX CONSULTING #{num5}",
            "STRIPE INCORPORATION LEGAL",
        ],
        450.00,
        3800.00,
        5,
    ),
    (
        "High Risk / Personal",
        [
            "CASINO HOTEL LAS VEGAS {state}",
            "BELLAGIO RESORT & CASINO",
            "WYNN LAS VEGAS CASINO",
            "ROLEX BOUTIQUE #{num3} {city}",
            "VIP LOUNGE NIGHTCLUB #{num4}",
            "GOLDEN NUGGET CASINO #{num4}",
        ],
        250.00,
        2400.00,
        3,
    ),
    (
        "Utilities",
        [
            "AT&T MOBILITY {phone}",
            "VERIZON WIRELESS #{num5}",
            "COMCAST BUSINESS #{num6}",
            "PG&E UTILITY BILL #{num8}",
        ],
        85.00,
        420.00,
        2,
    ),
]


def generate_benchmark_dataset(count: int = 1000, seed: int = 42) -> list[Transaction]:
    """Generate realistic bank transactions with POS terminal noise and diverse categories."""
    rnd = random.Random(seed)
    categories, templates_list, min_amts, max_amts, weights = zip(*MERCHANT_POOLS)

    transactions: list[Transaction] = []
    base_date = datetime.date(2026, 3, 1)

    cities = ["SAN FRANCISCO", "NEW YORK", "AUSTIN", "SEATTLE", "BOSTON", "CHICAGO"]
    states = ["CA", "NY", "TX", "WA", "MA", "IL"]
    accounts = ["Chase Sapphire Reserve", "Brex Corporate Card", "Mercury Business Checking", "Amex Platinum Business"]

    for i in range(count):
        # Pick category based on weights
        cat_idx = rnd.choices(range(len(categories)), weights=weights)[0]
        templates = templates_list[cat_idx]
        template = rnd.choice(templates)

        city = rnd.choice(cities)
        state = rnd.choice(states)
        phone = f"{rnd.randint(800, 888)}-{rnd.randint(200, 999)}-{rnd.randint(1000, 9999)}"
        num3 = f"{rnd.randint(100, 999)}"
        num4 = f"{rnd.randint(1000, 9999)}"
        num5 = f"{rnd.randint(10000, 99999)}"
        num6 = f"{rnd.randint(100000, 999999)}"
        num8 = f"{rnd.randint(10000000, 99999999)}"
        code5 = f"{rnd.randint(10, 99)}{rnd.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}{rnd.randint(10, 99)}"

        raw_desc = template.format(
            phone=phone,
            num3=num3,
            num4=num4,
            num5=num5,
            num6=num6,
            num8=num8,
            code5=code5,
            city=city,
            state=state,
        )

        min_a = min_amts[cat_idx]
        max_a = max_amts[cat_idx]
        amount = round(rnd.uniform(min_a, max_a), 2)
        date_offset = rnd.randint(0, 30)
        txn_date = base_date + datetime.timedelta(days=date_offset)
        account = rnd.choice(accounts)

        clean_desc = clean_merchant_string(raw_desc)
        txn_id = f"tx_{i+1:05d}_{uuid.uuid4().hex[:6]}"

        transactions.append(
            Transaction(
                id=txn_id,
                date=txn_date,
                raw_description=raw_desc,
                clean_description=clean_desc,
                amount=amount,
                currency="USD",
                account=account,
            )
        )

    return transactions


def save_benchmark_csv(dest_path: str | Path, count: int = 1000, seed: int = 42) -> Path:
    """Generate and save benchmark dataset as a standard CSV."""
    p = Path(dest_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    transactions = generate_benchmark_dataset(count=count, seed=seed)

    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Transaction ID", "Posting Date", "Description", "Amount", "Currency", "Account"])
        for t in transactions:
            writer.writerow([t.id, t.date.isoformat(), t.raw_description, f"{t.amount:.2f}", t.currency, t.account])

    return p
