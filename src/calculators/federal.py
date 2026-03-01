"""Federal Form 1040 tax calculator for tax year 2025."""

from decimal import Decimal

from src.calculators.schedules import (
    calculate_qdcg_worksheet,
    calculate_schedule_1,
    calculate_schedule_2,
    calculate_schedule_3,
    calculate_schedule_b,
    calculate_schedule_d,
    calculate_schedule_se,
)
from src.models import FederalTaxResult, TaxInput
from src.utils import (
    calculate_student_loan_deduction,
    calculate_tax_from_brackets,
    get_filing_status_constants,
)


def calculate_federal_tax(tax_input: TaxInput) -> FederalTaxResult:
    """Calculate complete federal tax return (Form 1040)."""
    result = FederalTaxResult()
    fsc = get_filing_status_constants(tax_input.filing_status)

    # ── Step 1: Aggregate income from source documents ──

    _Z = Decimal("0")
    wages = sum((w.wages_tips_other_comp for w in tax_input.w2s), _Z)
    interest_income = sum((f.box_1_interest_income for f in tax_input.forms_1099_int), _Z)
    tax_exempt_interest = sum(
        (f.box_8_tax_exempt_interest for f in tax_input.forms_1099_int), _Z
    )
    ordinary_dividends = sum(
        (f.box_1a_ordinary_dividends for f in tax_input.forms_1099_div), _Z
    )
    qualified_dividends = sum(
        (f.box_1b_qualified_dividends for f in tax_input.forms_1099_div), _Z
    )

    total_w2_ss_wages = sum((w.social_security_wages for w in tax_input.w2s), _Z)
    total_medicare_wages = sum((w.medicare_wages_and_tips for w in tax_input.w2s), _Z)
    # Add SE Medicare wages later if applicable

    # ── Step 2: Compute schedules ──

    schedule_b = calculate_schedule_b(tax_input)
    schedule_d = calculate_schedule_d(tax_input)
    schedule_se = calculate_schedule_se(tax_input, total_w2_ss_wages)

    # Compute student loan interest deduction from 1098-E forms
    # MAGI for student loan phase-out = AGI before the student loan deduction itself
    total_1098e_interest = sum(
        (f.box_1_student_loan_interest_paid for f in tax_input.forms_1098_e), _Z
    )
    nec_income = sum(
        (f.box_1_nonemployee_compensation for f in tax_input.forms_1099_nec), _Z
    )
    misc_income = sum((f.box_1_rents for f in tax_input.forms_1099_misc), _Z) + sum(
        (f.box_3_other_income for f in tax_input.forms_1099_misc), _Z
    )
    cap_gain = schedule_d.line_21_net_capital_gain_loss if schedule_d else _Z
    preliminary_income = wages + interest_income + ordinary_dividends + cap_gain + nec_income + misc_income
    se_deduction = schedule_se.line_13_deductible_half if schedule_se else _Z
    early_withdrawal = sum(
        (f.box_2_early_withdrawal_penalty for f in tax_input.forms_1099_int), _Z
    )
    preliminary_magi = preliminary_income - se_deduction - early_withdrawal

    student_loan_deduction = calculate_student_loan_deduction(
        total_1098e_interest,
        preliminary_magi,
        fsc["student_loan_phaseout_start"],
        fsc["student_loan_phaseout_end"],
    )

    schedule_1 = calculate_schedule_1(tax_input, schedule_se, student_loan_deduction)
    schedule_3 = calculate_schedule_3(tax_input, fsc["foreign_tax_credit_limit"])

    # ── Step 3: Build income section (Lines 1-9) ──

    result.line_1a_wages = wages
    result.line_2a_tax_exempt_interest = tax_exempt_interest
    result.line_2b_taxable_interest = interest_income
    result.line_3a_qualified_dividends = qualified_dividends
    result.line_3b_ordinary_dividends = ordinary_dividends

    # Line 7: Capital gain/loss from Schedule D
    if schedule_d:
        result.line_7_capital_gain_loss = schedule_d.line_21_net_capital_gain_loss

    # Line 8: Other income from Schedule 1
    if schedule_1:
        result.line_8_other_income = schedule_1.line_10_total_additional_income

    result.line_9_total_income = (
        result.line_1a_wages
        + result.line_2b_taxable_interest
        + result.line_3b_ordinary_dividends
        + result.line_7_capital_gain_loss
        + result.line_8_other_income
    )

    # ── Step 4: Adjustments and AGI (Lines 10-11) ──

    if schedule_1:
        result.line_10_adjustments = schedule_1.line_26_total_adjustments

    result.line_11_adjusted_gross_income = (
        result.line_9_total_income - result.line_10_adjustments
    )

    # ── Step 5: Deductions and taxable income (Lines 12-15) ──

    result.line_12_standard_deduction = fsc["standard_deduction"]
    result.line_14_total_deductions = (
        result.line_12_standard_deduction
        + result.line_13_qualified_business_deduction
    )
    result.line_15_taxable_income = max(
        Decimal("0"),
        result.line_11_adjusted_gross_income - result.line_14_total_deductions,
    )

    # ── Step 6: Tax computation (Line 16) ──

    # Determine if we need the QDCG worksheet
    net_ltcg = schedule_d.line_15_net_long_term if schedule_d else Decimal("0")
    has_preferential = qualified_dividends > 0 or net_ltcg > 0

    if has_preferential and result.line_15_taxable_income > 0:
        qdcg = calculate_qdcg_worksheet(
            result.line_15_taxable_income,
            qualified_dividends,
            net_ltcg,
            federal_brackets=fsc["federal_brackets"],
            ltcg_0_threshold=fsc["ltcg_0_threshold"],
            ltcg_15_threshold=fsc["ltcg_15_threshold"],
        )
        result.line_16_tax = qdcg.line_25_total_tax
        result.qdcg_worksheet = qdcg
    else:
        result.line_16_tax = calculate_tax_from_brackets(
            result.line_15_taxable_income, fsc["federal_brackets"]
        )

    # ── Step 7: Schedule 2 (additional taxes) ──

    # Net investment income for NIIT
    net_investment_income = (
        interest_income
        + ordinary_dividends
        + max(Decimal("0"), result.line_7_capital_gain_loss)
        + sum((f.box_1_rents for f in tax_input.forms_1099_misc), _Z)
        + sum((f.box_3_other_income for f in tax_input.forms_1099_misc), _Z)
    )

    # Total Medicare wages including SE income for additional Medicare
    se_medicare_wages = Decimal("0")
    if schedule_se:
        se_medicare_wages = schedule_se.line_3_92_35_pct
    combined_medicare_wages = total_medicare_wages + se_medicare_wages

    schedule_2 = calculate_schedule_2(
        schedule_se, combined_medicare_wages, net_investment_income,
        result.line_11_adjusted_gross_income,
        additional_medicare_threshold=fsc["additional_medicare_threshold"],
        niit_threshold=fsc["niit_threshold"],
    )

    # ── Step 8: Credits and total tax (Lines 17-24) ──

    if schedule_2:
        result.line_17_schedule_2_part1 = schedule_2.line_3_total
    result.line_18_sum = result.line_16_tax + result.line_17_schedule_2_part1

    if schedule_3:
        result.line_20_schedule_3_part1 = schedule_3.line_7_total
    result.line_21_total_credits = (
        result.line_19_child_credit + result.line_20_schedule_3_part1
    )
    result.line_22_after_credits = max(
        Decimal("0"), result.line_18_sum - result.line_21_total_credits
    )
    if schedule_2:
        result.line_23_other_taxes = schedule_2.line_21_total_additional_taxes
    result.line_24_total_tax = result.line_22_after_credits + result.line_23_other_taxes

    # ── Step 9: Payments (Lines 25-33) ──

    result.line_25a_w2_withheld = sum(
        (w.federal_income_tax_withheld for w in tax_input.w2s), _Z
    )
    result.line_25b_1099_withheld = (
        sum((f.box_4_federal_tax_withheld for f in tax_input.forms_1099_int), _Z)
        + sum((f.box_4_federal_tax_withheld for f in tax_input.forms_1099_div), _Z)
        + sum((f.box_4_federal_tax_withheld for f in tax_input.forms_1099_nec), _Z)
        + sum((f.box_4_federal_tax_withheld for f in tax_input.forms_1099_misc), _Z)
        + sum(
            (f.total_federal_tax_withheld for f in tax_input.forms_1099_b), _Z
        )
    )
    result.line_25d_total_withheld = (
        result.line_25a_w2_withheld + result.line_25b_1099_withheld
    )
    result.line_33_total_payments = result.line_25d_total_withheld

    # ── Step 10: Refund or amount owed (Lines 34-37) ──

    if result.line_33_total_payments > result.line_24_total_tax:
        result.line_34_overpayment = (
            result.line_33_total_payments - result.line_24_total_tax
        )
        result.line_35a_refund = result.line_34_overpayment
    else:
        result.line_37_amount_owed = (
            result.line_24_total_tax - result.line_33_total_payments
        )

    # ── Store schedule details ──

    result.schedule_1 = schedule_1
    result.schedule_2 = schedule_2
    result.schedule_3 = schedule_3
    result.schedule_b = schedule_b
    result.schedule_d = schedule_d
    result.schedule_se = schedule_se

    return result
