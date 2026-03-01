"""Tests for questionnaire features: dependents, charitable, estimated payments."""

from decimal import Decimal

from src.calculators.federal import calculate_federal_tax
from src.calculators.california import calculate_california_tax
from src.models import Dependent, TaxInput, W2, W2Box14
from src.utils import calculate_child_tax_credit


def _base_input(**overrides) -> TaxInput:
    """$150k single filer as base."""
    defaults = dict(
        first_name="Test",
        last_name="User",
        ssn="111-22-3333",
        state="CA",
        w2s=[
            W2(
                employer_ein="11-2233344",
                employer_name="Employer",
                employee_ssn="111-22-3333",
                employee_name="Test User",
                wages_tips_other_comp=Decimal("150000"),
                federal_income_tax_withheld=Decimal("28000"),
                social_security_wages=Decimal("150000"),
                social_security_tax_withheld=Decimal("9300"),
                medicare_wages_and_tips=Decimal("150000"),
                medicare_tax_withheld=Decimal("2175"),
                box_14_other=[W2Box14(description="CA SDI", amount=Decimal("1800"))],
                state="CA",
                state_wages=Decimal("150000"),
                state_income_tax=Decimal("9000"),
            )
        ],
    )
    defaults.update(overrides)
    return TaxInput(**defaults)


class TestChildTaxCredit:
    """Test Child Tax Credit calculations."""

    def test_no_dependents(self):
        result = calculate_federal_tax(_base_input())
        assert result.line_19_child_credit == Decimal("0")

    def test_one_child_under_17(self):
        ti = _base_input(dependents=[
            Dependent(name="Child One", ssn="999-88-7777", relationship="son", age=5)
        ])
        result = calculate_federal_tax(ti)
        assert result.line_19_child_credit == Decimal("2200")

    def test_two_children(self):
        ti = _base_input(dependents=[
            Dependent(name="Child One", ssn="999-88-7777", relationship="son", age=5),
            Dependent(name="Child Two", ssn="999-88-6666", relationship="daughter", age=10),
        ])
        result = calculate_federal_tax(ti)
        assert result.line_19_child_credit == Decimal("4400")

    def test_child_17_gets_other_credit(self):
        ti = _base_input(dependents=[
            Dependent(name="Teen", ssn="999-88-7777", relationship="son", age=17),
        ])
        result = calculate_federal_tax(ti)
        # Age 17 = other dependent credit ($500), not child tax credit ($2000)
        assert result.line_19_child_credit == Decimal("500")

    def test_mixed_ages(self):
        ti = _base_input(dependents=[
            Dependent(name="Young", ssn="999-88-7777", relationship="son", age=5),
            Dependent(name="Old", ssn="999-88-6666", relationship="daughter", age=20),
        ])
        result = calculate_federal_tax(ti)
        # $2,200 for child under 17 + $500 for other dependent
        assert result.line_19_child_credit == Decimal("2700")

    def test_credit_reduces_tax(self):
        no_kids = calculate_federal_tax(_base_input())
        with_kids = calculate_federal_tax(_base_input(dependents=[
            Dependent(name="Child", ssn="999-88-7777", relationship="son", age=5),
        ]))
        assert with_kids.line_24_total_tax < no_kids.line_24_total_tax


class TestChildTaxCreditPhaseout:
    """Test CTC phase-out for high income (single: $200k threshold)."""

    def test_below_threshold_full_credit(self):
        credit = calculate_child_tax_credit(
            [Dependent(name="X", ssn="1", relationship="son", age=5)],
            agi=Decimal("150000"),
            phaseout_start=Decimal("200000"),
        )
        assert credit == Decimal("2200")

    def test_above_threshold_reduced(self):
        credit = calculate_child_tax_credit(
            [Dependent(name="X", ssn="1", relationship="son", age=5)],
            agi=Decimal("210000"),
            phaseout_start=Decimal("200000"),
        )
        # $10k over threshold → 10 × $50 = $500 reduction → $2,200 - $500 = $1,700
        assert credit == Decimal("1700")

    def test_far_above_threshold_zero(self):
        credit = calculate_child_tax_credit(
            [Dependent(name="X", ssn="1", relationship="son", age=5)],
            agi=Decimal("300000"),
            phaseout_start=Decimal("200000"),
        )
        # $100k over → 100 × $50 = $5,000 reduction → $2,200 - $5,000 = $0
        assert credit == Decimal("0")


class TestCharitableContributions:
    """Test charitable contributions in Schedule A."""

    def test_charitable_increases_itemized(self):
        ti = _base_input(charitable_contributions_cash=Decimal("20000"))
        result = calculate_federal_tax(ti)
        assert result.schedule_a is not None
        assert result.schedule_a.line_12_charitable_cash == Decimal("20000")
        # SALT $9,000 (capped at $9,000) + charitable $20,000 = $29,000 > $15,000 standard
        assert result.schedule_a.used_itemized is True


class TestEstimatedPayments:
    """Test estimated tax payments."""

    def test_federal_estimated_reduces_owed(self):
        without = calculate_federal_tax(_base_input())
        with_est = calculate_federal_tax(_base_input(federal_estimated_payments=Decimal("5000")))
        assert with_est.line_33_total_payments == without.line_33_total_payments + Decimal("5000")

    def test_ca_estimated_payments(self):
        ti = _base_input(ca_estimated_payments=Decimal("3000"))
        fed = calculate_federal_tax(ti)
        ca = calculate_california_tax(ti, fed)
        assert ca.ca_estimated_payments == Decimal("3000")
        # CA estimated payments should be included in total_payments
        ca_without = calculate_california_tax(_base_input(), calculate_federal_tax(_base_input()))
        assert ca.total_payments == ca_without.total_payments + Decimal("3000")
