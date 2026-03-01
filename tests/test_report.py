"""Tests for report generation."""

import tempfile
from pathlib import Path

from src.calculators.california import calculate_california_tax
from src.calculators.federal import calculate_federal_tax
from src.generators.report import TaxReportGenerator
from src.models import TaxReturn


class TestTextReport:
    def _make_return(self, tax_input):
        federal = calculate_federal_tax(tax_input)
        ca = calculate_california_tax(tax_input, federal)
        return TaxReturn(input_data=tax_input, federal=federal, california=ca)

    def test_generates_without_error(self, simple_w2_input):
        tr = self._make_return(simple_w2_input)
        gen = TaxReportGenerator(tr)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = gen.generate_text(Path(tmpdir) / "report.txt")
            assert path.exists()
            content = path.read_text()
            assert len(content) > 0

    def test_contains_sections(self, simple_w2_input):
        tr = self._make_return(simple_w2_input)
        gen = TaxReportGenerator(tr)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = gen.generate_text(Path(tmpdir) / "report.txt")
            content = path.read_text()
            assert "FORM 1040" in content
            assert "CALIFORNIA FORM 540" in content
            assert "TAX RETURN SUMMARY" in content
            assert "SOURCE DOCUMENT SUMMARY" in content

    def test_contains_amounts(self, simple_w2_input):
        tr = self._make_return(simple_w2_input)
        gen = TaxReportGenerator(tr)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = gen.generate_text(Path(tmpdir) / "report.txt")
            content = path.read_text()
            assert "$100,000" in content
            assert "$15,000" in content

    def test_investment_report_has_schedules(self, investment_input):
        tr = self._make_return(investment_input)
        gen = TaxReportGenerator(tr)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = gen.generate_text(Path(tmpdir) / "report.txt")
            content = path.read_text()
            assert "SCHEDULE B" in content
            assert "SCHEDULE D" in content

    def test_se_report_has_schedule_se(self, self_employed_input):
        tr = self._make_return(self_employed_input)
        gen = TaxReportGenerator(tr)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = gen.generate_text(Path(tmpdir) / "report.txt")
            content = path.read_text()
            assert "SCHEDULE SE" in content
            assert "SCHEDULE 1" in content


class TestPDFReport:
    def test_generates_pdf(self, simple_w2_input):
        tr = self._make_return(simple_w2_input)
        gen = TaxReportGenerator(tr)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = gen.generate_pdf(Path(tmpdir) / "report.pdf")
            assert path.exists()
            assert path.stat().st_size > 0

    def _make_return(self, tax_input):
        federal = calculate_federal_tax(tax_input)
        ca = calculate_california_tax(tax_input, federal)
        return TaxReturn(input_data=tax_input, federal=federal, california=ca)
