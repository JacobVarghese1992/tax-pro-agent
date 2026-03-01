# 2025 Tax Pro

> **This tool is purely experimental. Do not trust the output of this software to file your taxes.** The generated forms, calculations, and reports may contain errors and should never be submitted to the IRS, California FTB, or any tax authority without independent verification by a qualified tax professional.
>
> Tax laws are complex and change frequently. This software makes simplifying assumptions and does not cover all tax situations, credits, deductions, or edge cases. The authors of this repository accept no responsibility and cannot be held accountable for any consequences — financial, legal, or otherwise — resulting from the use of this tool or reliance on its output.
>
> **Always consult a qualified tax professional before filing your tax return.**

A tax preparation tool that uses an AI coding agent to extract data from W-2, 1099, and 1098 PDFs, then calculates and generates 2025 Federal Form 1040 and California Form 540 tax returns.

## How It Works

1. Drop your tax document PDFs (W-2s, 1099s, 1098s) into the `input/` directory
2. Run the `/tax-filing` skill in your coding agent
3. The agent reads each PDF, extracts all fields, assembles a structured JSON, runs the calculator, and presents your results

The `/tax-filing` skill handles the entire pipeline — you don't need to manually create any JSON files or run any commands.

### Supported Platforms

The skill in `.claude/skills/tax-filing/` uses the cross-platform agent skills format and works with:

- **Claude Code** (recommended — the skill was written and tested here)
- **GitHub Copilot** agent mode in VS Code
- **OpenAI Codex** CLI and IDE extension
- **Cursor**, and other agent platforms that support the skills standard

## Features

- **PDF extraction via Claude Code** — reads W-2, 1099-INT, 1099-DIV, 1099-NEC, 1099-B, 1099-MISC, 1099-SA, 1098, and 1098-E documents
- **Federal Form 1040** with Schedules A, 1, 2, 3, B, D, and Form 8949
- **California Form 540** with standard deduction and exemption credits
- Filing statuses: Single, Married Filing Jointly
- Capital gains/losses with wash sale tracking across Form 8949 categories (Box A/B/D/E)
- Qualified Dividends and Capital Gain Tax Worksheet
- Additional Medicare Tax and Net Investment Income Tax (Schedule 2)
- Schedule A itemized deductions (mortgage interest, SALT with $10k cap) vs standard deduction
- HSA distributions (1099-SA) with qualified/non-qualified handling and 20% penalty
- Student loan interest deduction (with AGI phase-out)
- Generates filled IRS/CA PDF forms, text reports, and PDF reports

## Installation

```bash
pip install -r requirements.txt
```

Requires Python 3.11+.

## Usage

### With Claude Code (recommended)

Place your tax PDFs in `input/`, then in Claude Code run:

```
/tax-filing
```

Claude will extract data from each PDF, confirm your filing status, generate `input/tax_data.json`, run the calculations, and present a summary of your federal and California returns.

### Manual (advanced)

If you already have a `tax_data.json` file (e.g. from a previous run), you can invoke the calculator directly:

```bash
python main.py --input input/tax_data.json --output output/
```

Add `--text-only` to skip PDF generation.

### Output

- `output/2025_tax_return.txt` — Human-readable text report
- `output/2025_tax_return.pdf` — PDF report
- `output/2025_tax_return_data.json` — Raw computation data (JSON)
- `output/forms/` — Filled IRS and CA tax form PDFs

## Running Tests

```bash
pytest
```

## Privacy Warning

**Never commit real tax documents or personal financial data to version control.** The `input/` and `output/` directories are gitignored by default.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
