"""Tests for schedule calculators."""

from decimal import Decimal

from src.calculators.schedules import (
    calculate_qdcg_worksheet,
    calculate_schedule_b,
    calculate_schedule_d,
    calculate_schedule_se,
)


class TestScheduleB:
    def test_not_required_below_threshold(self, simple_w2_input):
        result = calculate_schedule_b(simple_w2_input)
        assert result is None

    def test_generated_above_threshold(self, investment_input):
        result = calculate_schedule_b(investment_input)
        assert result is not None
        assert result.line_4_total_interest == Decimal("2000")
        assert result.line_6_total_dividends == Decimal("5000")


class TestScheduleD:
    def test_no_capital_gains(self, simple_w2_input):
        result = calculate_schedule_d(simple_w2_input)
        assert result is None

    def test_with_transactions(self, investment_input):
        result = calculate_schedule_d(investment_input)
        assert result is not None
        # Short-term: MSFT gain = 8000 - 7500 = 500
        assert result.line_7_net_short_term == Decimal("500")
        # Long-term: AAPL gain = 20000 - 15000 = 5000, plus cap gain dist = 1000
        assert result.line_15_net_long_term == Decimal("6000")
        assert result.line_21_net_capital_gain_loss == Decimal("6500")

    def test_capital_loss_limit(self, capital_loss_input):
        result = calculate_schedule_d(capital_loss_input)
        assert result is not None
        # Loss = 2000 - 15000 = -13000, limited to -3000
        assert result.line_16_combine == Decimal("-13000")
        assert result.line_21_net_capital_gain_loss == Decimal("-3000")


class TestScheduleSE:
    def test_no_se_income(self, simple_w2_input):
        result = calculate_schedule_se(simple_w2_input, Decimal("100000"))
        assert result is None

    def test_se_calculation(self, self_employed_input):
        result = calculate_schedule_se(self_employed_input, Decimal("0"))
        assert result is not None
        assert result.line_2_net_se_earnings == Decimal("80000")
        # 92.35% of 80000 = 73880
        assert result.line_3_92_35_pct == Decimal("73880")
        # SS: 12.4% of 73880 (under wage base) = 9161
        assert result.line_4a_ss_portion == Decimal("9161")
        # Medicare: 2.9% of 73880 = 2142 (rounded)
        assert result.line_4b_medicare_portion == Decimal("2143")
        # Total SE tax
        assert result.line_12_se_tax == Decimal("11304")
        # Deductible half
        assert result.line_13_deductible_half == Decimal("5652")

    def test_se_with_existing_w2_ss_wages(self, self_employed_input):
        # If W2 already covers $170k of SS wages, only $6,100 of SE income is SS-taxable
        result = calculate_schedule_se(self_employed_input, Decimal("170000"))
        assert result is not None
        remaining_base = Decimal("176100") - Decimal("170000")  # $6,100
        # SS portion should only be on min(73880, 6100)
        expected_ss = (remaining_base * Decimal("0.124")).quantize(Decimal("1"))
        assert result.line_4a_ss_portion == expected_ss


class TestQDCGWorksheet:
    def test_zero_income(self):
        result = calculate_qdcg_worksheet(Decimal("0"), Decimal("0"), Decimal("0"))
        assert result.line_25_total_tax == Decimal("0")

    def test_all_preferential(self):
        # $50,000 taxable income, all from qualified dividends
        result = calculate_qdcg_worksheet(
            Decimal("50000"), Decimal("50000"), Decimal("0")
        )
        # Ordinary income = 0, preferential = 50000
        assert result.line_6_ordinary_income == Decimal("0")
        # 0% up to $48,475, 15% on $1,525
        expected_tax = Decimal("0") + (Decimal("1525") * Decimal("0.15")).quantize(
            Decimal("1")
        )
        assert result.line_25_total_tax == expected_tax

    def test_mixed_ordinary_and_preferential(self):
        # $100,000 taxable: $70k ordinary from wages, $30k qualified dividends
        result = calculate_qdcg_worksheet(
            Decimal("100000"), Decimal("30000"), Decimal("0")
        )
        # Ordinary income = 70000, preferential = 30000
        assert result.line_6_ordinary_income == Decimal("70000")
        # Tax on preferential should be at 15% (since ordinary fills past 0% threshold)
        # Regular tax on $100k would be higher than QDCG tax
        assert result.line_25_total_tax > 0

    def test_preferential_produces_less_tax(self):
        # Compare QDCG tax vs regular bracket tax
        from src.constants import FEDERAL_BRACKETS_SINGLE
        from src.utils import calculate_tax_from_brackets

        taxable = Decimal("100000")
        regular_tax = calculate_tax_from_brackets(taxable, FEDERAL_BRACKETS_SINGLE)
        qdcg = calculate_qdcg_worksheet(taxable, Decimal("30000"), Decimal("0"))
        assert qdcg.line_25_total_tax <= regular_tax
