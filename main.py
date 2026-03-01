"""2025 Tax Pro - CLI Entry Point.

Usage:
    python main.py --input input/sample_tax_data.json --output output/
    python main.py --input input/sample_tax_data.json --output output/ --text-only
"""

import argparse
import json
import sys
from pathlib import Path

from src.calculators.california import calculate_california_tax
from src.calculators.federal import calculate_federal_tax
from src.extractors.pdf_data import load_tax_input
from src.generators.form_filler import IRSFormFiller
from src.generators.report import TaxReportGenerator
from src.models import TaxReturn


def main() -> None:
    parser = argparse.ArgumentParser(
        description="2025 Tax Pro - Federal & California Tax Calculator"
    )
    parser.add_argument(
        "--input", required=True, help="Path to tax_data.json (extracted from PDFs)"
    )
    parser.add_argument(
        "--output", default="output/", help="Output directory for reports"
    )
    parser.add_argument(
        "--text-only", action="store_true", help="Generate text report only (no PDF)"
    )
    args = parser.parse_args()

    # Load and validate input
    tax_input = load_tax_input(args.input)

    # Calculate federal taxes
    federal_result = calculate_federal_tax(tax_input)

    # Calculate California taxes
    ca_result = calculate_california_tax(tax_input, federal_result)

    # Assemble complete return
    tax_return = TaxReturn(
        input_data=tax_input,
        federal=federal_result,
        california=ca_result,
    )

    # Generate reports
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    generator = TaxReportGenerator(tax_return)

    text_path = generator.generate_text(output_dir / "2025_tax_return.txt")
    print(f"Text report generated: {text_path}")

    if not args.text_only:
        pdf_path = generator.generate_pdf(output_dir / "2025_tax_return.pdf")
        print(f"PDF report generated: {pdf_path}")

    # Generate filled IRS tax forms
    forms_dir = output_dir / "forms"
    filler = IRSFormFiller(tax_return)
    filled_forms = filler.generate_all(forms_dir)
    if filled_forms:
        print(f"\nFilled IRS/CA tax forms ({len(filled_forms)} forms):")
        for form_path in filled_forms:
            print(f"  {form_path}")

    # Save raw computation as JSON
    json_path = output_dir / "2025_tax_return_data.json"
    with open(json_path, "w") as f:
        f.write(tax_return.model_dump_json(indent=2))
    print(f"Computation data saved: {json_path}")

    # Print summary
    print(f"\n{'=' * 50}")
    print("TAX RETURN SUMMARY")
    print(f"{'=' * 50}")
    print(f"Federal AGI:          ${federal_result.line_11_adjusted_gross_income:>12,.2f}")
    print(f"Federal Total Tax:    ${federal_result.line_24_total_tax:>12,.2f}")
    print(f"Federal Withheld:     ${federal_result.line_25d_total_withheld:>12,.2f}")
    if federal_result.line_35a_refund > 0:
        print(f"Federal REFUND:       ${federal_result.line_35a_refund:>12,.2f}")
    else:
        print(f"Federal OWED:         ${federal_result.line_37_amount_owed:>12,.2f}")
    print()
    print(f"California AGI:       ${ca_result.ca_agi:>12,.2f}")
    print(f"California Total Tax: ${ca_result.total_ca_tax:>12,.2f}")
    print(f"California Payments:  ${ca_result.total_payments:>12,.2f}")
    if ca_result.refund > 0:
        print(f"California REFUND:    ${ca_result.refund:>12,.2f}")
    else:
        print(f"California OWED:      ${ca_result.amount_owed:>12,.2f}")


if __name__ == "__main__":
    main()
