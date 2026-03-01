"""Tests for federal tax calculator."""

from decimal import Decimal

from src.calculators.federal import calculate_federal_tax
from src.constants import FEDERAL_BRACKETS_SINGLE
from src.utils import calculate_tax_from_brackets


class TestBracketCalculation:
    def test_zero_income(self):
        assert calculate_tax_from_brackets(Decimal("0"), FEDERAL_BRACKETS_SINGLE) == 0

    def test_first_bracket_only(self):
        # $10,000 at 10%
        tax = calculate_tax_from_brackets(Decimal("10000"), FEDERAL_BRACKETS_SINGLE)
        assert tax == Decimal("1000")

    def test_two_brackets(self):
        # $30,000: 10% on $11,925 + 12% on $18,075
        tax = calculate_tax_from_brackets(Decimal("30000"), FEDERAL_BRACKETS_SINGLE)
        expected = Decimal("11925") * Decimal("0.10") + Decimal("18075") * Decimal(
            "0.12"
        )
        assert tax == expected.quantize(Decimal("1"))

    def test_85k_taxable_income(self):
        # The simple W2 scenario: $85,000 taxable income
        # 10% on $11,925 = $1,192.50
        # 12% on ($48,475 - $11,925) = $4,386.00
        # 22% on ($85,000 - $48,475) = $8,035.50
        # Total = $13,614
        tax = calculate_tax_from_brackets(Decimal("85000"), FEDERAL_BRACKETS_SINGLE)
        assert tax == Decimal("13614")


class TestSimpleW2Only:
    def test_wages(self, simple_w2_input):
        result = calculate_federal_tax(simple_w2_input)
        assert result.line_1a_wages == Decimal("100000")

    def test_agi(self, simple_w2_input):
        result = calculate_federal_tax(simple_w2_input)
        assert result.line_11_adjusted_gross_income == Decimal("100000")

    def test_taxable_income(self, simple_w2_input):
        result = calculate_federal_tax(simple_w2_input)
        # AGI $100k - standard deduction $15k = $85k
        assert result.line_15_taxable_income == Decimal("85000")

    def test_tax(self, simple_w2_input):
        result = calculate_federal_tax(simple_w2_input)
        assert result.line_16_tax == Decimal("13614")

    def test_total_tax(self, simple_w2_input):
        result = calculate_federal_tax(simple_w2_input)
        # No additional taxes for $100k single filer
        assert result.line_24_total_tax == Decimal("13614")

    def test_withholding(self, simple_w2_input):
        result = calculate_federal_tax(simple_w2_input)
        assert result.line_25a_w2_withheld == Decimal("15000")
        assert result.line_25d_total_withheld == Decimal("15000")

    def test_refund(self, simple_w2_input):
        result = calculate_federal_tax(simple_w2_input)
        # Withheld $15,000 - tax $13,614 = refund $1,386
        assert result.line_35a_refund == Decimal("1386")
        assert result.line_37_amount_owed == Decimal("0")

    def test_no_schedules(self, simple_w2_input):
        result = calculate_federal_tax(simple_w2_input)
        assert result.schedule_1 is None
        assert result.schedule_se is None
        assert result.schedule_d is None


class TestWithInvestments:
    def test_income_lines(self, investment_input):
        result = calculate_federal_tax(investment_input)
        assert result.line_1a_wages == Decimal("150000")
        assert result.line_2b_taxable_interest == Decimal("2000")
        assert result.line_3b_ordinary_dividends == Decimal("5000")
        assert result.line_3a_qualified_dividends == Decimal("3500")

    def test_capital_gains(self, investment_input):
        result = calculate_federal_tax(investment_input)
        # Short-term: 500, Long-term: 5000 + 1000 cap dist = 6500 total
        assert result.line_7_capital_gain_loss == Decimal("6500")

    def test_schedule_b_created(self, investment_input):
        result = calculate_federal_tax(investment_input)
        assert result.schedule_b is not None

    def test_schedule_d_created(self, investment_input):
        result = calculate_federal_tax(investment_input)
        assert result.schedule_d is not None

    def test_qdcg_worksheet_used(self, investment_input):
        result = calculate_federal_tax(investment_input)
        # Has qualified dividends, so QDCG worksheet should be used
        assert result.qdcg_worksheet is not None

    def test_foreign_tax_credit(self, investment_input):
        result = calculate_federal_tax(investment_input)
        # $50 from 1099-INT + $100 from 1099-DIV = $150
        assert result.schedule_3 is not None
        assert result.schedule_3.line_1_foreign_tax_credit == Decimal("150")


class TestSelfEmployed:
    def test_schedule_se(self, self_employed_input):
        result = calculate_federal_tax(self_employed_input)
        assert result.schedule_se is not None
        assert result.schedule_se.line_12_se_tax > 0

    def test_schedule_1(self, self_employed_input):
        result = calculate_federal_tax(self_employed_input)
        assert result.schedule_1 is not None
        assert result.schedule_1.line_3_business_income == Decimal("80000")

    def test_se_deduction_in_adjustments(self, self_employed_input):
        result = calculate_federal_tax(self_employed_input)
        # Half of SE tax should be an adjustment
        assert result.line_10_adjustments == result.schedule_se.line_13_deductible_half

    def test_se_tax_in_schedule_2(self, self_employed_input):
        result = calculate_federal_tax(self_employed_input)
        assert result.schedule_2 is not None
        assert result.schedule_2.line_6_se_tax == result.schedule_se.line_12_se_tax


class TestHighIncome:
    def test_additional_medicare(self, high_income_input):
        result = calculate_federal_tax(high_income_input)
        assert result.schedule_2 is not None
        # 0.9% on ($400k - $200k) = $1,800
        assert result.schedule_2.line_11_additional_medicare == Decimal("1800")

    def test_niit(self, high_income_input):
        result = calculate_federal_tax(high_income_input)
        # AGI > $200k and has investment income
        assert result.schedule_2.line_17_niit > 0


class TestCapitalLoss:
    def test_loss_limited(self, capital_loss_input):
        result = calculate_federal_tax(capital_loss_input)
        # Loss of $13k limited to -$3k
        assert result.line_7_capital_gain_loss == Decimal("-3000")

    def test_loss_reduces_income(self, capital_loss_input):
        result = calculate_federal_tax(capital_loss_input)
        # AGI = $75k - $3k = $72k
        assert result.line_11_adjusted_gross_income == Decimal("72000")
