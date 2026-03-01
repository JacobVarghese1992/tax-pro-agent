"""Tests for data model validation."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models import (
    Form1099BTransaction,
    TaxInput,
    TermType,
    W2,
)


class TestW2Model:
    def test_required_fields(self):
        with pytest.raises(ValidationError):
            W2()  # Missing required fields

    def test_valid_w2(self, simple_w2_input):
        w2 = simple_w2_input.w2s[0]
        assert w2.wages_tips_other_comp == Decimal("100000")
        assert w2.employer_name == "Acme Corp"

    def test_defaults(self):
        w2 = W2(
            employer_ein="12-3456789",
            employer_name="Test",
            employee_ssn="123-45-6789",
            employee_name="Test User",
            wages_tips_other_comp=Decimal("50000"),
            federal_income_tax_withheld=Decimal("5000"),
            social_security_wages=Decimal("50000"),
            social_security_tax_withheld=Decimal("3100"),
            medicare_wages_and_tips=Decimal("50000"),
            medicare_tax_withheld=Decimal("725"),
        )
        assert w2.social_security_tips == Decimal("0")
        assert w2.statutory_employee is False
        assert w2.box_12_codes == []
        assert w2.box_14_other == []


class TestForm1099BTransaction:
    def test_gain_loss_computed(self):
        t = Form1099BTransaction(
            description="100 AAPL",
            proceeds=Decimal("15000"),
            cost_basis=Decimal("10000"),
            term=TermType.LONG_TERM,
        )
        assert t.gain_or_loss == Decimal("5000")

    def test_gain_loss_with_wash_sale(self):
        t = Form1099BTransaction(
            description="50 TSLA",
            proceeds=Decimal("5000"),
            cost_basis=Decimal("8000"),
            wash_sale_loss_disallowed=Decimal("1000"),
            term=TermType.SHORT_TERM,
        )
        # gain = 5000 - 8000 + 1000 = -2000
        assert t.gain_or_loss == Decimal("-2000")

    def test_explicit_gain_loss_preserved(self):
        t = Form1099BTransaction(
            description="Bond",
            proceeds=Decimal("10000"),
            cost_basis=Decimal("9500"),
            gain_or_loss=Decimal("600"),  # Explicitly set
            term=TermType.SHORT_TERM,
        )
        assert t.gain_or_loss == Decimal("600")


class TestTaxInput:
    def test_defaults(self):
        ti = TaxInput(first_name="A", last_name="B", ssn="111-22-3333")
        assert ti.tax_year == 2025
        assert ti.filing_status == "single"
        assert ti.state == "CA"
        assert ti.w2s == []
        assert ti.forms_1099_int == []

    def test_with_documents(self, simple_w2_input):
        assert len(simple_w2_input.w2s) == 1
        assert simple_w2_input.first_name == "John"
