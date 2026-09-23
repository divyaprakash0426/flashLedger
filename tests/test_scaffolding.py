"""Test package scaffolding and metadata."""

import importlib.metadata

def test_version_defined():
    import flash_ledger
    # Verify module has version or falls back
    assert hasattr(flash_ledger, "__version__")
    assert flash_ledger.__version__ == "0.1.0"
