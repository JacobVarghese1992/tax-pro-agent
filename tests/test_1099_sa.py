"""Tests for Form 1099-SA (HSA distributions) support."""

from decimal import Decimal

from src.calculators.federal import calculate_federal_tax
from src.models import Form1099SA, TaxInput, W2, W2Box14


def _make_with_hsa(qualified: bool, distribution: Decimal = Decimal("5000")) -> TaxInput:
    """W2 at $100k + HSA distribution."""
    return TaxInput(
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
                wages_tips_other_comp=Decimal("100000"),
                federal_income_tax_withheld=Decimal("15000"),
                social_security_wages=Decimal("100000"),
                social_security_tax_withheld=Decimal("6200"),
                medicare_wages_and_tips=Decimal("100000"),
                medicare_tax_withheld=Decimal("1450"),
                box_14_other=[W2Box14(description="CA SDI", amount=Decimal("1200"))],
                state="CA",
                state_wages=Decimal("100000"),
                state_income_tax=Decimal("5500"),
            )
        ],
        forms_1099_sa=[
            Form1099SA(
                payer_name="HSA Bank",
                recipient_name="Test User",
                recipient_tin="111-22-3333",
                box_1_gross_distribution=distribution,
                box_3_distribution_code="1",
                box_5_account_type="HSA",
                qualified=qualified,
            )
        ],
    )


class TestQualifiedHSA:
    """Qualified HSA distributions should have no tax impact."""

    def test_no_income_added(self):
        result = calculate_federal_tax(_make_with_hsa(qualified=True))
        # AGI should be just wages ($100,000), no HSA added
        assert result.line_11_adjusted_gross_income == Decimal("100000")

    def test_no_penalty(self):
        result = calculate_federal_tax(_make_with_hsa(qualified=True))
        # No additional taxes from HSA
        assert result.schedule_2 is None


class TestNonQualifiedHSA:
    """Non-qualified HSA distributions should be taxable + 20% penalty."""

    def test_income_added(self):
        result = calculate_federal_tax(_make_with_hsa(qualified=False))
        # AGI should include the $5,000 distribution
        assert result.line_11_adjusted_gross_income == Decimal("105000")

    def test_penalty_applied(self):
        result = calculate_federal_tax(_make_with_hsa(qualified=False))
        # 20% of $5,000 = $1,000 penalty
        assert result.schedule_2 is not None
        assert result.schedule_2.line_21_total_additional_taxes == Decimal("1000")

    def test_shows_in_other_income(self):
        result = calculate_federal_tax(_make_with_hsa(qualified=False))
        # $5,000 flows through Schedule 1 as other income
        assert result.line_8_other_income == Decimal("5000")
