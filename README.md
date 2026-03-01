# 2025 Tax Pro

A Python CLI tool that calculates and generates 2025 Federal Form 1040 and California Form 540 tax returns from structured tax document data.

## Features

- **Federal Form 1040** with Schedules 1, 2, 3, B, D, and Form 8949
- **California Form 540** with standard deduction and exemption credits
- Supports W-2, 1099-INT, 1099-DIV, 1099-NEC, 1099-B, 1099-MISC, and 1098-E
- Filing statuses: Single, Married Filing Jointly
- Capital gains/losses with wash sale tracking across Form 8949 categories (Box A/B/D/E)
- Qualified Dividends and Capital Gain Tax Worksheet
- Additional Medicare Tax and Net Investment Income Tax (Schedule 2)
- Student loan interest deduction (with AGI phase-out)
- Generates filled IRS/CA PDF forms, text reports, and PDF reports

## Installation

```bash
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
```

Requires Python 3.11+.

## Usage

Prepare your tax data as a JSON file (see `input/sample_tax_data.json` for the schema), then run:

```bash
python main.py --input input/sample_tax_data.json --output output/
```

For text report only (no PDF generation):

```bash
python main.py --input input/sample_tax_data.json --output output/ --text-only
```

### Output

- `output/2025_tax_return.txt` - Human-readable text report
- `output/2025_tax_return.pdf` - PDF report
- `output/2025_tax_return_data.json` - Raw computation data (JSON)
- `output/forms/` - Filled IRS and CA tax form PDFs

## Input Format

The input JSON file contains all extracted tax document data. See `input/sample_tax_data.json` for a complete example with fake data. Key fields:

- `filing_status`: `"single"` or `"married_filing_jointly"`
- `w2s`: Array of W-2 wage statements
- `forms_1099_int`: Array of 1099-INT interest income forms
- `forms_1099_div`: Array of 1099-DIV dividend forms
- `forms_1099_b`: Array of 1099-B brokerage transaction forms
- `forms_1098_e`: Array of 1098-E student loan interest forms

## Running Tests

```bash
pytest
```

## Privacy Warning

**Never commit real tax documents or personal financial data to version control.** The `input/` and `output/` directories are gitignored by default. The included `sample_tax_data.json` contains only fake data for testing purposes.

## Disclaimer

This software is provided for educational and personal use only. It is **not** professional tax advice. Tax laws are complex and change frequently. Always consult a qualified tax professional before filing your tax return. The authors are not responsible for any errors in tax calculations or any consequences of using this software.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
