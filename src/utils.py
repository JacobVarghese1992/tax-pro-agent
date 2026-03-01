"""Utility functions for tax calculations."""

from decimal import Decimal, ROUND_HALF_UP

from src.constants import (
    ADDITIONAL_MEDICARE_THRESHOLD_MFJ,
    ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
    CA_BRACKETS_MFJ,
    CA_BRACKETS_SINGLE,
    CA_MENTAL_HEALTH_THRESHOLD,
    CA_MENTAL_HEALTH_THRESHOLD_MFJ,
    CA_PERSONAL_EXEMPTION_CREDIT,
    CA_PERSONAL_EXEMPTION_CREDIT_MFJ,
    CA_STANDARD_DEDUCTION_MFJ,
    CA_STANDARD_DEDUCTION_SINGLE,
    CHILD_TAX_CREDIT_AMOUNT,
    CHILD_TAX_CREDIT_PHASEOUT_RATE,
    CHILD_TAX_CREDIT_PHASEOUT_START_MFJ,
    CHILD_TAX_CREDIT_PHASEOUT_START_SINGLE,
    FEDERAL_BRACKETS_MFJ,
    FEDERAL_BRACKETS_SINGLE,
    FEDERAL_STANDARD_DEDUCTION_MFJ,
    FEDERAL_STANDARD_DEDUCTION_SINGLE,
    FOREIGN_TAX_CREDIT_SIMPLIFIED_LIMIT,
    FOREIGN_TAX_CREDIT_SIMPLIFIED_LIMIT_MFJ,
    LTCG_0_THRESHOLD,
    LTCG_0_THRESHOLD_MFJ,
    LTCG_15_THRESHOLD,
    LTCG_15_THRESHOLD_MFJ,
    NIIT_THRESHOLD_MFJ,
    NIIT_THRESHOLD_SINGLE,
    OTHER_DEPENDENT_CREDIT_AMOUNT,
    STUDENT_LOAN_INTEREST_MAX_DEDUCTION,
    STUDENT_LOAN_PHASEOUT_END_MFJ,
    STUDENT_LOAN_PHASEOUT_END_SINGLE,
    STUDENT_LOAN_PHASEOUT_START_MFJ,
    STUDENT_LOAN_PHASEOUT_START_SINGLE,
)


def calculate_tax_from_brackets(
    taxable_income: Decimal,
    brackets: list[tuple[Decimal, Decimal]],
) -> Decimal:
    """Calculate tax using progressive brackets.

    Args:
        taxable_income: The taxable income amount.
        brackets: List of (upper_limit, rate) tuples, sorted ascending.

    Returns:
        Total tax rounded to the nearest dollar.
    """
    if taxable_income <= 0:
        return Decimal("0")

    tax = Decimal("0")
    prev_limit = Decimal("0")
    for upper_limit, rate in brackets:
        if taxable_income <= prev_limit:
            break
        taxable_in_bracket = min(taxable_income, upper_limit) - prev_limit
        tax += taxable_in_bracket * rate
        prev_limit = upper_limit

    return tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def round_dollar(amount: Decimal) -> Decimal:
    """Round to nearest dollar."""
    return amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def get_filing_status_constants(filing_status: str) -> dict:
    """Return all filing-status-dependent constants as a dict.

    Keys: federal_brackets, standard_deduction, ltcg_0_threshold,
    ltcg_15_threshold, additional_medicare_threshold, niit_threshold,
    foreign_tax_credit_limit, ca_brackets, ca_standard_deduction,
    ca_exemption_credit, ca_mental_health_threshold,
    student_loan_phaseout_start, student_loan_phaseout_end.
    """
    if filing_status == "married_filing_jointly":
        return {
            "federal_brackets": FEDERAL_BRACKETS_MFJ,
            "standard_deduction": FEDERAL_STANDARD_DEDUCTION_MFJ,
            "ltcg_0_threshold": LTCG_0_THRESHOLD_MFJ,
            "ltcg_15_threshold": LTCG_15_THRESHOLD_MFJ,
            "additional_medicare_threshold": ADDITIONAL_MEDICARE_THRESHOLD_MFJ,
            "niit_threshold": NIIT_THRESHOLD_MFJ,
            "foreign_tax_credit_limit": FOREIGN_TAX_CREDIT_SIMPLIFIED_LIMIT_MFJ,
            "child_tax_credit_phaseout_start": CHILD_TAX_CREDIT_PHASEOUT_START_MFJ,
            "ca_brackets": CA_BRACKETS_MFJ,
            "ca_standard_deduction": CA_STANDARD_DEDUCTION_MFJ,
            "ca_exemption_credit": CA_PERSONAL_EXEMPTION_CREDIT_MFJ,
            "ca_mental_health_threshold": CA_MENTAL_HEALTH_THRESHOLD_MFJ,
            "student_loan_phaseout_start": STUDENT_LOAN_PHASEOUT_START_MFJ,
            "student_loan_phaseout_end": STUDENT_LOAN_PHASEOUT_END_MFJ,
        }
    else:  # single
        return {
            "federal_brackets": FEDERAL_BRACKETS_SINGLE,
            "standard_deduction": FEDERAL_STANDARD_DEDUCTION_SINGLE,
            "ltcg_0_threshold": LTCG_0_THRESHOLD,
            "ltcg_15_threshold": LTCG_15_THRESHOLD,
            "additional_medicare_threshold": ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
            "niit_threshold": NIIT_THRESHOLD_SINGLE,
            "foreign_tax_credit_limit": FOREIGN_TAX_CREDIT_SIMPLIFIED_LIMIT,
            "child_tax_credit_phaseout_start": CHILD_TAX_CREDIT_PHASEOUT_START_SINGLE,
            "ca_brackets": CA_BRACKETS_SINGLE,
            "ca_standard_deduction": CA_STANDARD_DEDUCTION_SINGLE,
            "ca_exemption_credit": CA_PERSONAL_EXEMPTION_CREDIT,
            "ca_mental_health_threshold": CA_MENTAL_HEALTH_THRESHOLD,
            "student_loan_phaseout_start": STUDENT_LOAN_PHASEOUT_START_SINGLE,
            "student_loan_phaseout_end": STUDENT_LOAN_PHASEOUT_END_SINGLE,
        }


def calculate_child_tax_credit(
    dependents: list,
    agi: Decimal,
    phaseout_start: Decimal,
) -> Decimal:
    """Calculate Child Tax Credit (Form 1040 Line 19).

    $2,000 per qualifying child under 17, $500 per other dependent.
    Reduced by $50 for each $1,000 (or fraction) of AGI over the threshold.
    """
    qualifying_children = sum(1 for d in dependents if d.age < 17)
    other_dependents = sum(1 for d in dependents if d.age >= 17)

    total_credit = (
        qualifying_children * CHILD_TAX_CREDIT_AMOUNT
        + other_dependents * OTHER_DEPENDENT_CREDIT_AMOUNT
    )

    if total_credit <= 0:
        return Decimal("0")

    if agi > phaseout_start:
        excess = agi - phaseout_start
        # Reduce by $50 for each $1,000 (or fraction thereof)
        reduction_units = (excess + Decimal("999")) // Decimal("1000")
        reduction = reduction_units * CHILD_TAX_CREDIT_PHASEOUT_RATE
        total_credit = max(Decimal("0"), total_credit - reduction)

    return round_dollar(total_credit)


def calculate_student_loan_deduction(
    total_interest: Decimal,
    magi: Decimal,
    phaseout_start: Decimal,
    phaseout_end: Decimal,
) -> Decimal:
    """Calculate student loan interest deduction with income phase-out.

    Caps at $2,500, then reduces proportionally if MAGI is in phase-out range.
    Returns $0 if MAGI exceeds phase-out end.
    """
    if total_interest <= 0:
        return Decimal("0")

    deduction = min(total_interest, STUDENT_LOAN_INTEREST_MAX_DEDUCTION)

    if magi >= phaseout_end:
        return Decimal("0")
    elif magi > phaseout_start:
        phaseout_range = phaseout_end - phaseout_start
        excess = magi - phaseout_start
        reduction = deduction * excess / phaseout_range
        deduction = round_dollar(deduction - reduction)
        return max(Decimal("0"), deduction)

    return deduction
