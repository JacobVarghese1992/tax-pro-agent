"""Tests for California tax calculator."""

from decimal import Decimal

from src.calculators.california import calculate_california_tax
from src.calculators.federal import calculate_federal_tax
from src.constants import CA_BRACKETS_SINGLE
from src.utils import calculate_tax_from_brackets


class TestCABrackets:
    def test_zero_income(self):
        assert calculate_tax_from_brackets(Decimal("0"), CA_BRACKETS_SINGLE) == 0

    def test_first_bracket(self):
        # $10,000 at 1%
        tax = calculate_tax_from_brackets(Decimal("10000"), CA_BRACKETS_SINGLE)
        assert tax == Decimal("100")

    def test_94460_taxable(self):
        """The simple W2 scenario: CA taxable income $94,460."""
        # 1% on $10,756 = $107.56
        # 2% on ($25,499 - $10,756) = $294.86
        # 4% on ($40,245 - $25,499) = $589.84
        # 6% on ($55,866 - $40,245) = $937.26
        # 8% on ($70,606 - $55,866) = $1,179.20
        # 9.3% on ($94,460 - $70,606) = $2,218.42
        # Total = $5,327.14 -> $5,327
        tax = calculate_tax_from_brackets(Decimal("94460"), CA_BRACKETS_SINGLE)
        assert tax == Decimal("5327")


class TestSimpleW2California:
    def test_ca_agi(self, simple_w2_input):
        federal = calculate_federal_tax(simple_w2_input)
        ca = calculate_california_tax(simple_w2_input, federal)
        assert ca.ca_agi == Decimal("100000")

    def test_ca_taxable_income(self, simple_w2_input):
        federal = calculate_federal_tax(simple_w2_input)
        ca = calculate_california_tax(simple_w2_input, federal)
        # CA AGI $100k - CA std deduction $5,540 = $94,460
        assert ca.ca_taxable_income == Decimal("94460")

    def test_ca_tax(self, simple_w2_input):
        federal = calculate_federal_tax(simple_w2_input)
        ca = calculate_california_tax(simple_w2_input, federal)
        assert ca.ca_tax == Decimal("5327")

    def test_ca_exemption(self, simple_w2_input):
        federal = calculate_federal_tax(simple_w2_input)
        ca = calculate_california_tax(simple_w2_input, federal)
        assert ca.ca_exemption_credit == Decimal("149")
        assert ca.ca_tax_after_exemption == Decimal("5178")

    def test_ca_withholdings(self, simple_w2_input):
        federal = calculate_federal_tax(simple_w2_input)
        ca = calculate_california_tax(simple_w2_input, federal)
        assert ca.ca_tax_withheld == Decimal("5500")
        # SDI is not a credit unless excess from multiple employers
        assert ca.ca_sdi_withheld == Decimal("0")

    def test_ca_refund(self, simple_w2_input):
        federal = calculate_federal_tax(simple_w2_input)
        ca = calculate_california_tax(simple_w2_input, federal)
        # Total payments = 5500 (CA withholding only, SDI not a credit)
        # Tax = 5178
        # Refund = 5500 - 5178 = 322
        assert ca.total_payments == Decimal("5500")
        assert ca.refund == Decimal("322")


class TestCANoPreferentialRates:
    def test_all_income_ordinary(self, investment_input):
        """CA taxes all income at ordinary rates - no LTCG/qualified div preference."""
        federal = calculate_federal_tax(investment_input)
        ca = calculate_california_tax(investment_input, federal)
        # CA tax should be from regular bracket calculation on all income
        expected_tax = calculate_tax_from_brackets(
            ca.ca_taxable_income, CA_BRACKETS_SINGLE
        )
        assert ca.ca_tax == expected_tax


class TestCAUSBondSubtraction:
    def test_us_bond_interest_subtracted(self, high_income_input):
        """US Treasury bond interest should be subtracted from CA income."""
        federal = calculate_federal_tax(high_income_input)
        ca = calculate_california_tax(high_income_input, federal)
        # high_income fixture has $5,000 in US bond interest
        assert ca.ca_subtractions == Decimal("5000")
        assert ca.ca_agi == federal.line_11_adjusted_gross_income - Decimal("5000")


class TestCAMentalHealthSurcharge:
    def test_no_surcharge_below_threshold(self, simple_w2_input):
        federal = calculate_federal_tax(simple_w2_input)
        ca = calculate_california_tax(simple_w2_input, federal)
        assert ca.mental_health_surcharge == Decimal("0")

    def test_surcharge_above_1m(self):
        """Income over $1M triggers 1% mental health surcharge."""
        from tests.fixtures.sample_data import make_simple_w2_only

        ti = make_simple_w2_only()
        ti.w2s[0].wages_tips_other_comp = Decimal("1100000")
        ti.w2s[0].state_wages = Decimal("1100000")
        ti.w2s[0].social_security_wages = Decimal("176100")
        ti.w2s[0].medicare_wages_and_tips = Decimal("1100000")
        ti.w2s[0].federal_income_tax_withheld = Decimal("350000")
        ti.w2s[0].state_income_tax = Decimal("100000")

        federal = calculate_federal_tax(ti)
        ca = calculate_california_tax(ti, federal)
        # CA taxable = $1,100,000 - $5,540 = $1,094,460
        # Surcharge = 1% of ($1,094,460 - $1,000,000) = $945 (rounded)
        assert ca.mental_health_surcharge == Decimal("945")
