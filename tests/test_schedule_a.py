"""Tests for Schedule A (Itemized Deductions) and Form 1098 integration."""

from decimal import Decimal

import pytest

from src.calculators.federal import calculate_federal_tax
from src.calculators.california import calculate_california_tax
from src.calculators.schedules import calculate_schedule_a
from tests.fixtures.sample_data import (
    make_simple_w2_only,
    make_with_mortgage,
    make_with_small_mortgage,
)


class TestScheduleACalculation:
    """Test Schedule A calculation logic."""

    def test_no_1098_no_schedule_a_items(self):
        """Without mortgage or significant SALT, schedule_a still computed from state taxes."""
        ti = make_simple_w2_only()
        result = calculate_schedule_a(ti, Decimal("15750"))
        # W2 has $5,500 state tax, which gives SALT of $5,500
        # Total itemized = $5,500 < $15,000 standard, so not used
        assert result is not None
        assert result.line_5e_salt_deduction == Decimal("5500")
        assert result.line_17_total_itemized == Decimal("5500")
        assert result.used_itemized is False

    def test_mortgage_exceeds_standard(self):
        """Large mortgage interest + SALT should exceed standard deduction."""
        ti = make_with_mortgage()
        result = calculate_schedule_a(ti, Decimal("15750"))
        # $14,000 state tax + $8,000 property tax = $22,000 SALT
        # OBBB $40,000 cap (AGI defaults to 0, no phasedown), so full $22,000
        # $18,000 mortgage interest
        # Total = $22,000 + $18,000 = $40,000 > $15,750 standard
        assert result is not None
        assert result.line_5a_state_local_income_tax == Decimal("14000")
        assert result.line_5b_state_local_property_tax == Decimal("8000")
        assert result.line_5d_salt_total == Decimal("22000")
        assert result.line_5e_salt_deduction == Decimal("22000")
        assert result.line_8a_mortgage_interest_1098 == Decimal("18000")
        assert result.line_10_total_interest == Decimal("18000")
        assert result.line_17_total_itemized == Decimal("40000")
        assert result.used_itemized is True

    def test_small_mortgage_uses_standard(self):
        """Small mortgage + SALT should not exceed standard deduction."""
        ti = make_with_small_mortgage()
        result = calculate_schedule_a(ti, Decimal("15750"))
        # $5,500 state tax, SALT capped at $5,500
        # $3,000 mortgage interest
        # Total = $5,500 + $3,000 = $8,500 < $15,000 standard
        assert result is not None
        assert result.line_17_total_itemized == Decimal("8500")
        assert result.used_itemized is False

    def test_salt_cap_at_40000(self):
        """SALT deduction should be capped at $40,000 (OBBB Act)."""
        ti = make_with_mortgage()
        result = calculate_schedule_a(ti, Decimal("15750"))
        # State income tax $14,000 + property tax $8,000 = $22,000
        # Under $40,000 cap, so full amount is deductible
        assert result.line_5d_salt_total == Decimal("22000")
        assert result.line_5e_salt_deduction == Decimal("22000")

    def test_salt_phasedown_high_income(self):
        """SALT cap phases down for AGI over $500,000."""
        ti = make_with_mortgage()
        # AGI $600k: excess = $100k, reduction = 30% × $100k = $30k
        # Cap = $40k - $30k = $10k
        result = calculate_schedule_a(ti, Decimal("15750"), agi=Decimal("600000"))
        assert result.line_5d_salt_total == Decimal("22000")
        assert result.line_5e_salt_deduction == Decimal("10000")


class TestFederalWithMortgage:
    """Test federal calculator integration with Schedule A."""

    def test_itemized_deduction_used(self):
        """Federal tax should use itemized deductions when they exceed standard."""
        ti = make_with_mortgage()
        result = calculate_federal_tax(ti)
        assert result.schedule_a is not None
        assert result.schedule_a.used_itemized is True
        # SALT: $22,000 (under $40k OBBB cap, AGI $200k < $500k phasedown)
        # Mortgage: $18,000. Total = $40,000 itemized > $15,750 standard
        assert result.line_14_total_deductions == Decimal("40000")

    def test_standard_deduction_when_mortgage_small(self):
        """Federal tax should use standard deduction when it exceeds itemized."""
        ti = make_with_small_mortgage()
        result = calculate_federal_tax(ti)
        assert result.schedule_a is not None
        assert result.schedule_a.used_itemized is False
        assert result.line_14_total_deductions == Decimal("15750")

    def test_no_1098_uses_standard(self):
        """Without any 1098, standard deduction should still be used."""
        ti = make_simple_w2_only()
        result = calculate_federal_tax(ti)
        assert result.line_14_total_deductions == Decimal("15750")


class TestCaliforniaWithMortgage:
    """Test California calculator with Schedule A."""

    def test_ca_itemized_includes_mortgage_property_charitable(self):
        """CA itemized should include mortgage interest + property tax + charitable."""
        ti = make_with_mortgage()
        fed = calculate_federal_tax(ti)
        ca = calculate_california_tax(ti, fed)
        # CA itemized = $18,000 mortgage + $8,000 property tax + $0 charitable = $26,000
        # CA standard = $5,706
        # $26,000 > $5,706, so CA should itemize
        assert ca.ca_used_itemized is True
        assert ca.ca_itemized_deduction == Decimal("26000")

    def test_ca_standard_when_mortgage_small(self):
        """CA should use standard deduction when itemized < CA standard deduction."""
        ti = make_with_small_mortgage()
        fed = calculate_federal_tax(ti)
        ca = calculate_california_tax(ti, fed)
        # Small mortgage fixture has no property tax, $3,000 mortgage < $5,706 standard
        assert ca.ca_used_itemized is False
