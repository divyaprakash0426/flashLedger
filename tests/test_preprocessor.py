"""Unit tests for flash_ledger.preprocessor."""

import io
from pathlib import Path
from flash_ledger.preprocessor import clean_merchant_string, parse_amount, parse_statement_csv

def test_clean_merchant_string():
    test_cases = [
        ("SQ *BLUE BOTTLE SOMA", "Blue Bottle"),
        ("AMZN Mktp US*284J1", "Amazon"),
        ("GITHUB*SPONSOR 877-448", "Github Sponsor"),
        ("TST* TARTINE BAKERY #104", "Tartine Bakery"),
        ("UBER *TRIP 12345 SAN FRANCISCO CA", "Uber Trip"),
        ("PAYPAL *SLACK TECH 408-555-0199", "Slack Tech"),
        ("DRI*OPENAI LLC *SUBSCRIPTION", "Openai"),
        ("APPLE STORE #104 800-692-7753 CA", "Apple Store"),
        ("CASINO HOTEL LAS VEGAS NV", "Casino Hotel Las Vegas"),
    ]
    for raw, expected_prefix in test_cases:
        cleaned = clean_merchant_string(raw)
        assert cleaned.lower().startswith(expected_prefix.lower()), f"Expected '{cleaned}' to start with '{expected_prefix}' for raw '{raw}'"

def test_parse_amount():
    assert parse_amount(14.20) == 14.20
    assert parse_amount("14.20") == 14.20
    assert parse_amount("$1,299.00") == 1299.00
    assert parse_amount("£4,878.20") == 4878.20
    assert parse_amount("(15.50)") == -15.50
    assert parse_amount("-850.00") == -850.00
    assert parse_amount("  $ 45.00  ") == 45.00

def test_parse_chase_csv(tmp_path):
    csv_content = """Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #
DEBIT,03/15/2026,SQ *BLUE BOTTLE SOMA,14.20,Sale,1200.00,
DEBIT,03/16/2026,AMZN Mktp US*284J1,45.99,Sale,1154.01,
CREDIT,03/17/2026,REFUND SUPPLIES,-25.00,Refund,1179.01,
"""
    file_path = tmp_path / "chase.csv"
    file_path.write_text(csv_content)

    txns = parse_statement_csv(file_path)
    assert len(txns) == 3
    assert txns[0].raw_description == "SQ *BLUE BOTTLE SOMA"
    assert "Blue Bottle" in txns[0].clean_description
    assert txns[0].amount == 14.20
    assert txns[2].amount == -25.00

def test_parse_uk_gov_csv(tmp_path):
    csv_content = """Department Family,Entity,Date,Expense Type,Expense Area,Supplier,Transaction Number,Amount,Description
Department for Education,Core,05/03/2024,Other Costs,Operational Finance,Agile Management Solutions Ltd,CORE-PINV-074083,"4,878.20",Software Development
Department for Education,Core,05/03/2024,Travel,Operations,British Airways,CORE-PINV-074084,"650.00",Flight to Edinburgh
"""
    file_path = tmp_path / "uk_gov.csv"
    file_path.write_text(csv_content)

    txns = parse_statement_csv(file_path)
    assert len(txns) == 2
    assert "Agile Management" in txns[0].clean_description
    assert txns[0].amount == 4878.20
    assert txns[1].amount == 650.00
    assert txns[1].currency == "GBP"
