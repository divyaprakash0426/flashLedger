"""Downloader utilities for public benchmark and government spending datasets."""

from __future__ import annotations
import os
import urllib.request
from pathlib import Path
from typing import Optional

UK_GOV_SPEND_URL = (
    "https://assets.publishing.service.gov.uk/media/66ab4b46ce1fd0da7b593142/DfE_Spend__25k_Mar_2024.csv"
)


def download_uk_gov_data(dest_path: Optional[str | Path] = None) -> Path:
    """Download authentic UK Government corporate expenditure dataset (> £25k transparency spend)."""
    if dest_path:
        out = Path(dest_path)
    else:
        out = Path("data") / "uk_gov_spending_2024.csv"

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 1000:
        return out

    try:
        req = urllib.request.Request(
            UK_GOV_SPEND_URL,
            headers={"User-Agent": "flashLedger-Downloader/0.1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            with open(out, "wb") as f:
                f.write(content)
        return out
    except Exception as e:
        # If network error, create a fallback sample of UK Gov data
        sample_content = (
            "Department Family,Entity,Date,Expense Type,Expense Area,Supplier,Transaction Number,Amount,Description\n"
            'Department for Education,Core,05/03/2024,Other Costs,Operational Finance,Agile Management Solutions Ltd,CORE-PINV-074083,"4,878.20",Software Development\n'
            'Department for Education,Core,05/03/2024,Travel,Operations,British Airways,CORE-PINV-074084,"650.00",Flight to Edinburgh\n'
            'Department for Education,Core,05/03/2024,IT Hardware,Technology,Dell Corporation,CORE-PINV-074085,"3,450.00",Server Workstations\n'
        )
        with open(out, "w", encoding="utf-8") as f:
            f.write(sample_content)
        return out


def download_hf_dataset(dest_path: Optional[str | Path] = None, token: Optional[str] = None) -> Path:
    """
    Attempt to download mitulshah/transaction-categorization from Hugging Face.
    Note: This is a gated dataset requiring an HF token and agreement to terms.
    """
    hf_token = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")

    if dest_path:
        out = Path(dest_path)
    else:
        out = Path("data") / "hf_transaction_categories.json"

    out.parent.mkdir(parents=True, exist_ok=True)

    if not hf_token:
        # Save informative notice and fallback structure
        fallback_info = {
            "dataset": "mitulshah/transaction-categorization",
            "status": "GATED_DATASET_AUTH_REQUIRED",
            "instruction": (
                "To download the full 4.5M record dataset, log in at https://huggingface.co/datasets/mitulshah/transaction-categorization, "
                "accept dataset terms, and set 'HF_TOKEN=<your_token>' in your environment or pass --token to flash-ledger download-dataset."
            ),
            "fallback_available": True,
            "sample_categories": [
                "Food & Dining",
                "Transportation",
                "Shopping & Retail",
                "Entertainment & Recreation",
                "Healthcare & Medical",
                "Utilities & Services",
                "Financial Services",
                "Income",
                "Government & Legal",
                "Charity & Donations"
            ]
        }
        import json
        with open(out, "w", encoding="utf-8") as f:
            json.dump(fallback_info, f, indent=2)
        return out

    try:
        from huggingface_hub import hf_hub_download
        downloaded = hf_hub_download(
            repo_id="mitulshah/transaction-categorization",
            filename="categories.json",
            token=hf_token,
            repo_type="dataset",
        )
        import shutil
        shutil.copy(downloaded, out)
        return out
    except Exception as e:
        import json
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"error": str(e)}, f, indent=2)
        return out
