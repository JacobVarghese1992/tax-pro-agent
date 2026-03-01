"""Schedule calculators: B, D, SE, 1, 2, 3, and QDCG worksheet."""

from decimal import Decimal

from src.constants import (
    ADDITIONAL_MEDICARE_RATE,
    ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
    CAPITAL_LOSS_LIMIT,
    FEDERAL_BRACKETS_SINGLE,
    FOREIGN_TAX_CREDIT_SIMPLIFIED_LIMIT,
    HSA_NONQUALIFIED_PENALTY_RATE,
    LTCG_0_THRESHOLD,
    LTCG_15_THRESHOLD,
    MEDICARE_RATE_SELF_EMPLOYED,
    NIIT_RATE,
    NIIT_THRESHOLD_SINGLE,
    SALT_DEDUCTION_LIMIT,
    SCHEDULE_B_THRESHOLD,
    SE_INCOME_FACTOR,
    SS_RATE_SELF_EMPLOYED,
    SS_WAGE_BASE,
)
from src.models import (
    BasisReportedToIRS,
    QDCGWorksheet,
    Schedule1Result,
    Schedule2Result,
    Schedule3Result,
    ScheduleAResult,
    ScheduleBItem,
    ScheduleBResult,
    ScheduleDResult,
    ScheduleSEResult,
    TaxInput,
    TermType,
)
from src.utils import calculate_tax_from_brackets, round_dollar


def calculate_schedule_a(
    tax_input: TaxInput, standard_deduction: Decimal
) -> ScheduleAResult | None:
    """Calculate Schedule A: Itemized Deductions.

    Computes itemized deductions from Form 1098 mortgage interest,
    state/local taxes (SALT), and points. Compares against the standard
    deduction and sets used_itemized=True if itemizing is beneficial.

    Returns None if no itemizable deductions exist.
    """
    _Z = Decimal("0")

    # Lines 5a: State and local income taxes paid (from W-2 box 17 + 1099 state withholding)
    state_income_tax = sum((w.state_income_tax for w in tax_input.w2s), _Z)
    for f in tax_input.forms_1099_int:
        state_income_tax += f.state_tax_withheld
    for f in tax_input.forms_1099_div:
        state_income_tax += f.state_tax_withheld
    for f in tax_input.forms_1099_nec:
        state_income_tax += f.state_income_tax_withheld
    for f in tax_input.forms_1099_misc:
        state_income_tax += f.state_tax_withheld

    # Line 5b: State and local property taxes (from 1098 box 10)
    property_tax = sum((f.box_10_property_tax for f in tax_input.forms_1098), _Z)

    # Line 5d: Total SALT before cap
    salt_total = state_income_tax + property_tax

    # Line 5e: SALT deduction (capped at $10,000)
    salt_deduction = min(salt_total, SALT_DEDUCTION_LIMIT)

    # Lines 8a, 8c: Mortgage interest and points from Form 1098
    mortgage_interest = sum((f.box_1_mortgage_interest for f in tax_input.forms_1098), _Z)
    points = sum((f.box_6_points_paid for f in tax_input.forms_1098), _Z)
    total_interest = mortgage_interest + points

    # Lines 12: Charitable contributions (cash)
    charitable_cash = tax_input.charitable_contributions_cash

    # Line 17: Total itemized deductions
    total_itemized = salt_deduction + total_interest + charitable_cash

    if total_itemized == _Z:
        return None

    used_itemized = total_itemized > standard_deduction

    return ScheduleAResult(
        line_5a_state_local_income_tax=state_income_tax,
        line_5b_state_local_property_tax=property_tax,
        line_5d_salt_total=salt_total,
        line_5e_salt_deduction=salt_deduction,
        line_8a_mortgage_interest_1098=mortgage_interest,
        line_8c_points=points,
        line_10_total_interest=total_interest,
        line_12_charitable_cash=charitable_cash,
        line_17_total_itemized=total_itemized,
        used_itemized=used_itemized,
    )


def calculate_schedule_b(tax_input: TaxInput) -> ScheduleBResult | None:
    """Calculate Schedule B: Interest and Ordinary Dividends.

    Required when interest or dividends exceed $1,500.
    """
    interest_items = []
    total_interest = Decimal("0")
    for f in tax_input.forms_1099_int:
        if f.box_1_interest_income > 0:
            interest_items.append(
                ScheduleBItem(payer_name=f.payer_name, amount=f.box_1_interest_income)
            )
            total_interest += f.box_1_interest_income

    dividend_items = []
    total_dividends = Decimal("0")
    for f in tax_input.forms_1099_div:
        if f.box_1a_ordinary_dividends > 0:
            dividend_items.append(
                ScheduleBItem(
                    payer_name=f.payer_name, amount=f.box_1a_ordinary_dividends
                )
            )
            total_dividends += f.box_1a_ordinary_dividends

    if total_interest < SCHEDULE_B_THRESHOLD and total_dividends < SCHEDULE_B_THRESHOLD:
        return None

    return ScheduleBResult(
        interest_items=interest_items,
        line_4_total_interest=total_interest,
        dividend_items=dividend_items,
        line_6_total_dividends=total_dividends,
    )


def calculate_schedule_d(tax_input: TaxInput) -> ScheduleDResult | None:
    """Calculate Schedule D: Capital Gains and Losses."""
    has_1099b = any(f.transactions for f in tax_input.forms_1099_b)
    has_cap_gain_dist = any(
        f.box_2a_total_capital_gain > 0 for f in tax_input.forms_1099_div
    )
    if not has_1099b and not has_cap_gain_dist:
        return None

    st_reported = Decimal("0")
    st_not_reported = Decimal("0")
    lt_reported = Decimal("0")
    lt_not_reported = Decimal("0")

    for form in tax_input.forms_1099_b:
        for t in form.transactions:
            gain = t.gain_or_loss if t.gain_or_loss is not None else Decimal("0")
            is_reported = t.basis_reported_to_irs == BasisReportedToIRS.YES

            if t.term == TermType.SHORT_TERM:
                if is_reported:
                    st_reported += gain
                else:
                    st_not_reported += gain
            elif t.term == TermType.LONG_TERM:
                if is_reported:
                    lt_reported += gain
                else:
                    lt_not_reported += gain
            else:
                # Unknown term: default to short-term (conservative)
                if is_reported:
                    st_reported += gain
                else:
                    st_not_reported += gain

    net_short_term = st_reported + st_not_reported
    cap_gain_distributions = sum(
        (f.box_2a_total_capital_gain for f in tax_input.forms_1099_div), Decimal("0")
    )
    net_long_term = lt_reported + lt_not_reported + cap_gain_distributions

    combined = net_short_term + net_long_term
    # Apply $3,000 capital loss limit
    if combined < 0:
        net_gain_loss = max(combined, -CAPITAL_LOSS_LIMIT)
    else:
        net_gain_loss = combined

    return ScheduleDResult(
        line_1a_short_term_basis_reported=st_reported,
        line_1b_short_term_basis_not_reported=st_not_reported,
        line_7_net_short_term=net_short_term,
        line_8a_long_term_basis_reported=lt_reported,
        line_8b_long_term_basis_not_reported=lt_not_reported,
        line_11_capital_gain_distributions=cap_gain_distributions,
        line_15_net_long_term=net_long_term,
        line_16_combine=combined,
        line_21_net_capital_gain_loss=net_gain_loss,
    )


def calculate_schedule_se(
    tax_input: TaxInput, total_w2_ss_wages: Decimal
) -> ScheduleSEResult | None:
    """Calculate Schedule SE: Self-Employment Tax."""
    nec_income = sum(
        (f.box_1_nonemployee_compensation for f in tax_input.forms_1099_nec),
        Decimal("0"),
    )
    if nec_income <= 0:
        return None

    net_se = nec_income
    se_92_35 = round_dollar(net_se * SE_INCOME_FACTOR)

    # SS portion: only on amount up to wage base not covered by W2 wages
    remaining_ss_base = max(Decimal("0"), SS_WAGE_BASE - total_w2_ss_wages)
    ss_taxable = min(se_92_35, remaining_ss_base)
    ss_portion = round_dollar(ss_taxable * SS_RATE_SELF_EMPLOYED)

    medicare_portion = round_dollar(se_92_35 * MEDICARE_RATE_SELF_EMPLOYED)
    se_tax = ss_portion + medicare_portion
    deductible_half = round_dollar(se_tax / 2)

    return ScheduleSEResult(
        line_2_net_se_earnings=net_se,
        line_3_92_35_pct=se_92_35,
        line_4a_ss_portion=ss_portion,
        line_4b_medicare_portion=medicare_portion,
        line_12_se_tax=se_tax,
        line_13_deductible_half=deductible_half,
    )


def calculate_schedule_1(
    tax_input: TaxInput,
    schedule_se: ScheduleSEResult | None,
    student_loan_deduction: Decimal = Decimal("0"),
) -> Schedule1Result | None:
    """Calculate Schedule 1: Additional Income and Adjustments."""
    # Part I - Additional Income
    _Z = Decimal("0")
    business_income = sum(
        (f.box_1_nonemployee_compensation for f in tax_input.forms_1099_nec), _Z
    )
    rental_income = sum((f.box_1_rents for f in tax_input.forms_1099_misc), _Z)
    other_income = sum((f.box_3_other_income for f in tax_input.forms_1099_misc), _Z)

    # Non-qualified HSA distributions are taxable (Form 8889 → Schedule 1 Line 8z)
    nonqualified_hsa = sum(
        (f.box_1_gross_distribution for f in tax_input.forms_1099_sa if not f.qualified), _Z
    )
    other_income += nonqualified_hsa

    total_additional = business_income + rental_income + other_income

    # Part II - Adjustments
    se_deduction = schedule_se.line_13_deductible_half if schedule_se else Decimal("0")
    early_withdrawal = sum(
        (f.box_2_early_withdrawal_penalty for f in tax_input.forms_1099_int),
        Decimal("0"),
    )
    total_adjustments = se_deduction + early_withdrawal + student_loan_deduction

    if total_additional == 0 and total_adjustments == 0:
        return None

    return Schedule1Result(
        line_3_business_income=business_income,
        line_5_rental_income=rental_income,
        line_8a_other_income=other_income,
        line_10_total_additional_income=total_additional,
        line_15_se_tax_deduction=se_deduction,
        line_18_early_withdrawal_penalty=early_withdrawal,
        line_21_student_loan_interest=student_loan_deduction,
        line_26_total_adjustments=total_adjustments,
    )


def calculate_schedule_2(
    schedule_se: ScheduleSEResult | None,
    total_medicare_wages: Decimal,
    net_investment_income: Decimal,
    agi: Decimal,
    nonqualified_hsa: Decimal = Decimal("0"),
    additional_medicare_threshold: Decimal = ADDITIONAL_MEDICARE_THRESHOLD_SINGLE,
    niit_threshold: Decimal = NIIT_THRESHOLD_SINGLE,
) -> Schedule2Result | None:
    """Calculate Schedule 2: Additional Taxes."""
    se_tax = schedule_se.line_12_se_tax if schedule_se else Decimal("0")

    # Additional Medicare tax: 0.9% on Medicare wages over threshold
    excess_medicare = max(Decimal("0"), total_medicare_wages - additional_medicare_threshold)
    additional_medicare = round_dollar(excess_medicare * ADDITIONAL_MEDICARE_RATE)

    # NIIT: 3.8% on lesser of (net investment income, AGI - threshold)
    agi_excess = max(Decimal("0"), agi - niit_threshold)
    niit_base = min(net_investment_income, agi_excess)
    niit = round_dollar(max(Decimal("0"), niit_base) * NIIT_RATE)

    # HSA non-qualified distribution penalty: 20% (Form 8889 Part III)
    hsa_penalty = round_dollar(nonqualified_hsa * HSA_NONQUALIFIED_PENALTY_RATE)

    total = se_tax + additional_medicare + niit + hsa_penalty
    if total == 0:
        return None

    return Schedule2Result(
        line_6_se_tax=se_tax,
        line_11_additional_medicare=additional_medicare,
        line_17_niit=niit,
        line_21_total_additional_taxes=total,
    )


def calculate_schedule_3(
    tax_input: TaxInput,
    foreign_tax_credit_limit: Decimal = FOREIGN_TAX_CREDIT_SIMPLIFIED_LIMIT,
) -> Schedule3Result | None:
    """Calculate Schedule 3: Additional Credits."""
    foreign_tax = sum((f.box_6_foreign_tax_paid for f in tax_input.forms_1099_int), Decimal("0"))
    foreign_tax += sum((f.box_7_foreign_tax_paid for f in tax_input.forms_1099_div), Decimal("0"))

    # Simplified: take direct credit if under limit
    if foreign_tax <= 0:
        return None

    credit = min(foreign_tax, foreign_tax_credit_limit)
    return Schedule3Result(
        line_1_foreign_tax_credit=credit,
        line_7_total=credit,
    )


def calculate_qdcg_worksheet(
    taxable_income: Decimal,
    qualified_dividends: Decimal,
    net_ltcg: Decimal,
    federal_brackets: list[tuple[Decimal, Decimal]] = FEDERAL_BRACKETS_SINGLE,
    ltcg_0_threshold: Decimal = LTCG_0_THRESHOLD,
    ltcg_15_threshold: Decimal = LTCG_15_THRESHOLD,
) -> QDCGWorksheet:
    """Qualified Dividends and Capital Gain Tax Worksheet.

    Computes tax with preferential 0%/15%/20% rates on qualified income
    and ordinary rates on the rest.
    """
    if taxable_income <= 0:
        return QDCGWorksheet(line_1_taxable_income=taxable_income)

    # Line 1: taxable income
    # Line 2: qualified dividends
    # Line 3: net LTCG (positive only; from Schedule D line 15 if positive, else 0)
    net_ltcg_positive = max(Decimal("0"), net_ltcg)
    # Line 4: sum of qualified divs + LTCG
    line_4 = qualified_dividends + net_ltcg_positive
    # Line 5: preferential income = min(line_4, taxable_income)
    line_5 = min(line_4, taxable_income)
    # Line 6: ordinary income = taxable_income - preferential
    line_6 = taxable_income - line_5

    # Tax on ordinary income at regular rates
    tax_on_ordinary = calculate_tax_from_brackets(line_6, federal_brackets)

    # Tax on preferential income at 0%/15%/20%
    # The 0% bracket applies up to ltcg_0_threshold minus ordinary income
    remaining_0_space = max(Decimal("0"), ltcg_0_threshold - line_6)
    at_0_pct = min(line_5, remaining_0_space)

    remaining_15_space = max(Decimal("0"), ltcg_15_threshold - line_6 - at_0_pct)
    at_15_pct = min(line_5 - at_0_pct, remaining_15_space)

    at_20_pct = line_5 - at_0_pct - at_15_pct

    tax_on_preferential = round_dollar(
        at_0_pct * Decimal("0")
        + at_15_pct * Decimal("0.15")
        + at_20_pct * Decimal("0.20")
    )

    total_tax = tax_on_ordinary + tax_on_preferential

    # Also compute tax without preferential rates for comparison
    regular_tax = calculate_tax_from_brackets(taxable_income, federal_brackets)
    # Use the lesser of the two
    final_tax = min(total_tax, regular_tax)

    return QDCGWorksheet(
        line_1_taxable_income=taxable_income,
        line_2_qualified_dividends=qualified_dividends,
        line_3_net_ltcg=net_ltcg_positive,
        line_4_sum=line_4,
        line_5_investment_income=line_5,
        line_6_ordinary_income=line_6,
        line_9_tax_on_ordinary=tax_on_ordinary,
        line_25_total_tax=final_tax,
    )
