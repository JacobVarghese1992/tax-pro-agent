"""JSON loader/saver for extracted tax data."""

import json
from pathlib import Path

from src.models import TaxInput


def load_tax_input(json_path: str | Path) -> TaxInput:
    """Load and validate extracted tax data from a JSON file."""
    with open(json_path) as f:
        data = json.load(f)
    return TaxInput.model_validate(data)


def save_tax_input(tax_input: TaxInput, json_path: str | Path) -> None:
    """Save tax input data to JSON for inspection."""
    with open(json_path, "w") as f:
        f.write(tax_input.model_dump_json(indent=2))
