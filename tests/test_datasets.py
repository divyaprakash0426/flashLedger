"""Unit tests for flash_ledger.datasets."""

from pathlib import Path
from flash_ledger.datasets.synthetic import generate_benchmark_dataset, save_benchmark_csv
from flash_ledger.datasets.download import download_uk_gov_data

def test_generate_benchmark_dataset():
    txns = generate_benchmark_dataset(count=100)
    assert len(txns) == 100
    assert all(t.raw_description for t in txns)
    assert all(t.amount > 0 for t in txns)

    # Check for presence of variety: SaaS, meals, capex, high-risk
    descriptions = " ".join(t.raw_description.lower() for t in txns)
    assert "apple" in descriptions or "dell" in descriptions
    assert "aws" in descriptions or "github" in descriptions or "slack" in descriptions
    assert "coffee" in descriptions or "bottle" in descriptions or "starbucks" in descriptions

def test_save_benchmark_csv(tmp_path):
    out_file = tmp_path / "sample_100.csv"
    path = save_benchmark_csv(out_file, count=100)
    assert path.exists()
    assert path.stat().st_size > 1000
