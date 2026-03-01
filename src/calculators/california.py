"""California Form 540 tax calculator for tax year 2025."""

from decimal import Decimal

from src.constants import CA_MENTAL_HEALTH_RATE
from src.models import CaliforniaTaxResult, FederalTaxResult, TaxInput
from src.utils import calculate_tax_from_brackets, get_filing_status_constants, round_dollar


def calculate_california_tax(
    tax_input: TaxInput, federal: FederalTaxResult
) -> CaliforniaTaxResult:
    """Calculate California Form 540 tax return."""
    result = CaliforniaTaxResult()
    fsc = get_filing_status_constants(tax_input.filing_status)

    # ── Step 1: Start from Federal AGI ──

    result.federal_agi = federal.line_11_adjusted_gross_income

    # ── Step 2: California Additions ──
    # With standard deduction (no state/local tax deduction), additions are typically $0
    result.ca_additions = Decimal("0")

    # ── Step 3: California Subtractions ──
    # US Treasury bond interest is exempt from CA tax
    us_bond_interest = sum(
        (f.box_3_us_savings_bond_interest for f in tax_input.forms_1099_int),
        Decimal("0"),
    )
    result.ca_subtractions = us_bond_interest

    # ── Step 4: CA AGI and Taxable Income ──

    result.ca_agi = result.federal_agi + result.ca_additions - result.ca_subtractions
    result.ca_standard_deduction = fsc["ca_standard_deduction"]
    result.ca_taxable_income = max(
        Decimal("0"), result.ca_agi - result.ca_standard_deduction
    )

    # ── Step 5: CA Tax from Brackets ──
    # California does NOT have preferential rates for qualified dividends or LTCG
    result.ca_tax = calculate_tax_from_brackets(
        result.ca_taxable_income, fsc["ca_brackets"]
    )

    # ── Step 6: Credits ──

    result.ca_exemption_credit = fsc["ca_exemption_credit"]
    result.ca_tax_after_exemption = max(
        Decimal("0"), result.ca_tax - result.ca_exemption_credit
    )

    # ── Step 7: Mental Health Services Tax ──

    if result.ca_taxable_income > fsc["ca_mental_health_threshold"]:
        result.mental_health_surcharge = round_dollar(
            (result.ca_taxable_income - fsc["ca_mental_health_threshold"])
            * CA_MENTAL_HEALTH_RATE
        )

    # ── Step 8: Total CA Tax ──

    result.total_ca_tax = result.ca_tax_after_exemption + result.mental_health_surcharge

    # ── Step 9: Withholdings ──

    # State income tax withheld from W2s
    result.ca_tax_withheld = sum(
        (w.state_income_tax for w in tax_input.w2s if w.state == "CA"),
        Decimal("0"),
    )
    # Add state withholdings from 1099s
    for f in tax_input.forms_1099_int:
        if f.state == "CA":
            result.ca_tax_withheld += f.state_tax_withheld
    for f in tax_input.forms_1099_div:
        if f.state == "CA":
            result.ca_tax_withheld += f.state_tax_withheld
    for f in tax_input.forms_1099_nec:
        if f.state == "CA":
            result.ca_tax_withheld += f.state_income_tax_withheld
    for f in tax_input.forms_1099_misc:
        if f.state == "CA":
            result.ca_tax_withheld += f.state_tax_withheld

    # Excess SDI/VPDI (Line 74): Only claimable when a person had MULTIPLE
    # employers whose combined SDI exceeds the annual max. Since CA removed
    # the SDI wage ceiling in 2024, excess SDI is effectively $0 — each
    # employer withholds the flat rate on all wages, so multiple employers
    # never cause over-withholding. ca_sdi_withheld stays at its default $0.

    # ── Step 10: Refund or Amount Owed ──

    result.total_payments = (
        result.ca_tax_withheld
        + result.ca_estimated_payments
        + result.ca_sdi_withheld
    )

    if result.total_payments > result.total_ca_tax:
        result.overpaid = result.total_payments - result.total_ca_tax
        result.refund = result.overpaid
    else:
        result.amount_owed = result.total_ca_tax - result.total_payments

    return result
