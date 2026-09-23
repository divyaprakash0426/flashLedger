"""Unit tests for flash_ledger.coa."""

import json
from flash_ledger.coa import ChartOfAccounts, AccountDefinition

def test_load_default_coa():
    coa = ChartOfAccounts.load_default()
    assert len(coa.accounts) >= 10
    assert "Software/SaaS" in coa.account_names
    assert "Meals & Entertainment" in coa.account_names
    assert "Office Supplies" in coa.account_names

    saas = coa.get_account("Software/SaaS")
    assert saas is not None
    assert "software" in saas.description.lower() or "saas" in saas.description.lower()
    assert saas.tax_deductible_default is True

def test_custom_coa_loader(tmp_path):
    custom_data = {
        "name": "Custom Tech Startup COA",
        "capex_threshold": 3000.0,
        "accounts": [
            {
                "code": "6010",
                "name": "Cloud Infrastructure",
                "description": "AWS, GCP, Azure, and hosting fees",
                "tax_deductible_default": True,
                "category": "Technology",
            },
            {
                "code": "6020",
                "name": "Team Lunches",
                "description": "Catering and meals provided at office",
                "tax_deductible_default": True,
                "category": "Operations",
            }
        ]
    }
    file_path = tmp_path / "custom_coa.json"
    file_path.write_text(json.dumps(custom_data))

    coa = ChartOfAccounts.load(file_path)
    assert coa.name == "Custom Tech Startup COA"
    assert coa.capex_threshold == 3000.0
    assert "Cloud Infrastructure" in coa.account_names
    assert "Team Lunches" in coa.account_names
    assert coa.get_criteria_mapping()["Cloud Infrastructure"] == "AWS, GCP, Azure, and hosting fees"
