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
        # $14,000 state tax + $8,000 property tax = $22,000 SALT, capped at $10,000
        # $18,000 mortgage interest
        # Total = $10,000 + $18,000 = $28,000 > $15,000 standard
        assert result is not None
        assert result.line_5a_state_local_income_tax == Decimal("14000")
        assert result.line_5b_state_local_property_tax == Decimal("8000")
        assert result.line_5d_salt_total == Decimal("22000")
        assert result.line_5e_salt_deduction == Decimal("10000")
        assert result.line_8a_mortgage_interest_1098 == Decimal("18000")
        assert result.line_10_total_interest == Decimal("18000")
        assert result.line_17_total_itemized == Decimal("28000")
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

    def test_salt_cap_at_10000(self):
        """SALT deduction should be capped at $10,000."""
        ti = make_with_mortgage()
        result = calculate_schedule_a(ti, Decimal("15750"))
        # State income tax $14,000 + property tax $8,000 = $22,000
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
        # Total deductions = $28,000 itemized (not $15,000 standard)
        assert result.line_14_total_deductions == Decimal("28000")

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

    def test_ca_itemized_mortgage_only(self):
        """CA should use mortgage interest only (no SALT) for itemized deductions."""
        ti = make_with_mortgage()
        fed = calculate_federal_tax(ti)
        ca = calculate_california_tax(ti, fed)
        # CA itemized = mortgage interest $18,000 only (no SALT on state return)
        # CA standard = $5,540 (single)
        # $18,000 > $5,540, so CA should itemize
        assert ca.ca_used_itemized is True
        assert ca.ca_itemized_deduction == Decimal("18000")

    def test_ca_standard_when_mortgage_small(self):
        """CA should use standard deduction when mortgage < CA standard deduction."""
        ti = make_with_small_mortgage()
        fed = calculate_federal_tax(ti)
        ca = calculate_california_tax(ti, fed)
        # CA itemized = $3,000 mortgage < $5,540 standard
        assert ca.ca_used_itemized is False
