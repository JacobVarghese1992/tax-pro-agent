"""Tax return report generation (PDF and text)."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from src.models import TaxReturn


def _fmt(amount: Decimal) -> str:
    """Format a dollar amount with commas and sign."""
    if amount < 0:
        return f"(${abs(amount):,.0f})"
    return f"${amount:,.0f}"


def _line(label: str, amount: Decimal, width: int = 60) -> str:
    """Format a line item with dot leaders."""
    dots = "." * max(2, width - len(label) - len(_fmt(amount)))
    return f"  {label} {dots} {_fmt(amount)}"


class TaxReportGenerator:
    """Generates PDF and text tax return reports."""

    def __init__(self, tax_return: TaxReturn):
        self.tr = tax_return
        self.fed = tax_return.federal
        self.ca = tax_return.california
        self.inp = tax_return.input_data

    def generate_text(self, output_path: str | Path) -> Path:
        """Generate plain text report."""
        lines: list[str] = []
        a = lines.append

        a("=" * 64)
        a("    2025 FEDERAL & CALIFORNIA TAX RETURN")
        a(f"    Prepared: {date.today().isoformat()}")
        name = f"{self.inp.first_name} {self.inp.last_name}"
        ssn_masked = f"XXX-XX-{self.inp.ssn[-4:]}" if len(self.inp.ssn) >= 4 else "XXX-XX-XXXX"
        a(f"    Taxpayer: {name}  SSN: {ssn_masked}")
        if self.inp.filing_status == "married_filing_jointly" and self.inp.spouse_first_name:
            spouse_name = f"{self.inp.spouse_first_name} {self.inp.spouse_last_name}"
            spouse_ssn = self.inp.spouse_ssn or ""
            spouse_ssn_masked = f"XXX-XX-{spouse_ssn[-4:]}" if len(spouse_ssn) >= 4 else "XXX-XX-XXXX"
            a(f"    Spouse:   {spouse_name}  SSN: {spouse_ssn_masked}")
        filing_display = {"single": "Single", "married_filing_jointly": "Married Filing Jointly"}
        a(f"    Filing Status: {filing_display.get(self.inp.filing_status, self.inp.filing_status)}")
        a("=" * 64)

        # ── Source Document Summary ──
        a("")
        a("SECTION 1: SOURCE DOCUMENT SUMMARY")
        a("-" * 40)
        for w in self.inp.w2s:
            a(f"  W-2 from {w.employer_name}")
            a(f"    Box 1  Wages: {_fmt(w.wages_tips_other_comp)}")
            a(f"    Box 2  Federal tax withheld: {_fmt(w.federal_income_tax_withheld)}")
            a(f"    Box 3  SS wages: {_fmt(w.social_security_wages)}")
            a(f"    Box 5  Medicare wages: {_fmt(w.medicare_wages_and_tips)}")
            if w.state_wages:
                a(f"    Box 16 State wages ({w.state}): {_fmt(w.state_wages)}")
                a(f"    Box 17 State tax withheld: {_fmt(w.state_income_tax)}")
            for item in w.box_14_other:
                a(f"    Box 14 {item.description}: {_fmt(item.amount)}")
            a("")

        for f in self.inp.forms_1099_int:
            a(f"  1099-INT from {f.payer_name}")
            if f.box_1_interest_income:
                a(f"    Box 1  Interest income: {_fmt(f.box_1_interest_income)}")
            if f.box_3_us_savings_bond_interest:
                a(f"    Box 3  US bond interest: {_fmt(f.box_3_us_savings_bond_interest)}")
            if f.box_6_foreign_tax_paid:
                a(f"    Box 6  Foreign tax paid: {_fmt(f.box_6_foreign_tax_paid)}")
            if f.box_8_tax_exempt_interest:
                a(f"    Box 8  Tax-exempt interest: {_fmt(f.box_8_tax_exempt_interest)}")
            a("")

        for f in self.inp.forms_1099_div:
            a(f"  1099-DIV from {f.payer_name}")
            if f.box_1a_ordinary_dividends:
                a(f"    Box 1a Ordinary dividends: {_fmt(f.box_1a_ordinary_dividends)}")
            if f.box_1b_qualified_dividends:
                a(f"    Box 1b Qualified dividends: {_fmt(f.box_1b_qualified_dividends)}")
            if f.box_2a_total_capital_gain:
                a(f"    Box 2a Capital gain distributions: {_fmt(f.box_2a_total_capital_gain)}")
            if f.box_7_foreign_tax_paid:
                a(f"    Box 7  Foreign tax paid: {_fmt(f.box_7_foreign_tax_paid)}")
            a("")

        for f in self.inp.forms_1099_nec:
            a(f"  1099-NEC from {f.payer_name}")
            a(f"    Box 1  Nonemployee compensation: {_fmt(f.box_1_nonemployee_compensation)}")
            a("")

        for f in self.inp.forms_1099_b:
            a(f"  1099-B from {f.broker_name}")
            a(f"    {len(f.transactions)} transaction(s)")
            a(f"    Total proceeds: {_fmt(f.total_proceeds)}")
            a(f"    Total cost basis: {_fmt(f.total_cost_basis)}")
            a(f"    Net gain/loss: {_fmt(f.total_gain_loss)}")
            a("")

        for f in self.inp.forms_1099_misc:
            a(f"  1099-MISC from {f.payer_name}")
            if f.box_1_rents:
                a(f"    Box 1  Rents: {_fmt(f.box_1_rents)}")
            if f.box_3_other_income:
                a(f"    Box 3  Other income: {_fmt(f.box_3_other_income)}")
            a("")

        for f in self.inp.forms_1098:
            a(f"  1098 from {f.lender_name}")
            a(f"    Borrower: {f.borrower_name}")
            a(f"    Box 1  Mortgage interest: {_fmt(f.box_1_mortgage_interest)}")
            if f.box_6_points_paid:
                a(f"    Box 6  Points paid: {_fmt(f.box_6_points_paid)}")
            if f.box_10_property_tax:
                a(f"    Box 10 Property tax: {_fmt(f.box_10_property_tax)}")
            a("")

        for f in self.inp.forms_1098_e:
            a(f"  1098-E from {f.lender_name}")
            a(f"    Borrower: {f.borrower_name}")
            a(f"    Box 1  Student loan interest paid: {_fmt(f.box_1_student_loan_interest_paid)}")
            a("")

        # ── Form 1040 ──
        a("SECTION 2: FORM 1040 - U.S. INDIVIDUAL INCOME TAX RETURN")
        a("-" * 56)
        a("")
        a("INCOME")
        a(_line("Line 1a  Wages, salaries, tips", self.fed.line_1a_wages))
        a(_line("Line 2a  Tax-exempt interest", self.fed.line_2a_tax_exempt_interest))
        a(_line("Line 2b  Taxable interest", self.fed.line_2b_taxable_interest))
        a(_line("Line 3a  Qualified dividends", self.fed.line_3a_qualified_dividends))
        a(_line("Line 3b  Ordinary dividends", self.fed.line_3b_ordinary_dividends))
        a(_line("Line 7   Capital gain or (loss)", self.fed.line_7_capital_gain_loss))
        a(_line("Line 8   Other income (Sched 1)", self.fed.line_8_other_income))
        a(_line("Line 9   TOTAL INCOME", self.fed.line_9_total_income))
        a("")
        a("ADJUSTMENTS")
        a(_line("Line 10  Adjustments (Sched 1)", self.fed.line_10_adjustments))
        a(_line("Line 11  ADJUSTED GROSS INCOME", self.fed.line_11_adjusted_gross_income))
        a("")
        a("DEDUCTIONS")
        if self.fed.schedule_a and self.fed.schedule_a.used_itemized:
            a(_line("Line 12  Itemized deductions (Sched A)", self.fed.schedule_a.line_17_total_itemized))
        else:
            a(_line("Line 12  Standard deduction", self.fed.line_12_standard_deduction))
        a(_line("Line 14  Total deductions", self.fed.line_14_total_deductions))
        a(_line("Line 15  Taxable income", self.fed.line_15_taxable_income))
        a("")
        a("TAX AND CREDITS")
        a(_line("Line 16  Tax", self.fed.line_16_tax))
        a(_line("Line 17  Sched 2, Part I", self.fed.line_17_schedule_2_part1))
        a(_line("Line 18  Sum of 16 and 17", self.fed.line_18_sum))
        a(_line("Line 20  Credits (Sched 3)", self.fed.line_20_schedule_3_part1))
        a(_line("Line 22  After credits", self.fed.line_22_after_credits))
        a(_line("Line 23  Other taxes (Sched 2)", self.fed.line_23_other_taxes))
        a(_line("Line 24  TOTAL TAX", self.fed.line_24_total_tax))
        a("")
        a("PAYMENTS")
        a(_line("Line 25a W-2 withholding", self.fed.line_25a_w2_withheld))
        a(_line("Line 25b 1099 withholding", self.fed.line_25b_1099_withheld))
        a(_line("Line 25d Total withheld", self.fed.line_25d_total_withheld))
        a(_line("Line 33  TOTAL PAYMENTS", self.fed.line_33_total_payments))
        a("")
        a("RESULT")
        if self.fed.line_35a_refund > 0:
            a(_line("Line 35a REFUND", self.fed.line_35a_refund))
        elif self.fed.line_37_amount_owed > 0:
            a(_line("Line 37  AMOUNT OWED", self.fed.line_37_amount_owed))
        else:
            a("  No refund or amount owed (break even)")

        # ── Schedules ──
        if self.fed.schedule_1:
            s = self.fed.schedule_1
            a("")
            a("SCHEDULE 1: ADDITIONAL INCOME AND ADJUSTMENTS")
            a("-" * 48)
            if s.line_3_business_income:
                a(_line("Line 3   Business income", s.line_3_business_income))
            if s.line_5_rental_income:
                a(_line("Line 5   Rental income", s.line_5_rental_income))
            if s.line_8a_other_income:
                a(_line("Line 8a  Other income", s.line_8a_other_income))
            a(_line("Line 10  Total additional income", s.line_10_total_additional_income))
            if s.line_15_se_tax_deduction:
                a(_line("Line 15  SE tax deduction", s.line_15_se_tax_deduction))
            if s.line_18_early_withdrawal_penalty:
                a(_line("Line 18  Early withdrawal penalty", s.line_18_early_withdrawal_penalty))
            if s.line_21_student_loan_interest:
                a(_line("Line 21  Student loan interest", s.line_21_student_loan_interest))
            a(_line("Line 26  Total adjustments", s.line_26_total_adjustments))

        if self.fed.schedule_2:
            s = self.fed.schedule_2
            a("")
            a("SCHEDULE 2: ADDITIONAL TAXES")
            a("-" * 48)
            if s.line_6_se_tax:
                a(_line("Line 6   Self-employment tax", s.line_6_se_tax))
            if s.line_11_additional_medicare:
                a(_line("Line 11  Additional Medicare tax", s.line_11_additional_medicare))
            if s.line_17_niit:
                a(_line("Line 17  Net investment income tax", s.line_17_niit))
            a(_line("Line 21  Total additional taxes", s.line_21_total_additional_taxes))

        if self.fed.schedule_3:
            s = self.fed.schedule_3
            a("")
            a("SCHEDULE 3: ADDITIONAL CREDITS")
            a("-" * 48)
            a(_line("Line 1   Foreign tax credit", s.line_1_foreign_tax_credit))

        if self.fed.schedule_a:
            s = self.fed.schedule_a
            a("")
            a("SCHEDULE A: ITEMIZED DEDUCTIONS")
            a("-" * 48)
            a(_line("Line 5a  State/local income tax", s.line_5a_state_local_income_tax))
            if s.line_5b_state_local_property_tax:
                a(_line("Line 5b  Property tax", s.line_5b_state_local_property_tax))
            a(_line("Line 5d  Total SALT (before cap)", s.line_5d_salt_total))
            a(_line("Line 5e  SALT deduction (capped)", s.line_5e_salt_deduction))
            a(_line("Line 8a  Mortgage interest", s.line_8a_mortgage_interest_1098))
            if s.line_8c_points:
                a(_line("Line 8c  Points", s.line_8c_points))
            a(_line("Line 10  Total interest deduction", s.line_10_total_interest))
            a(_line("Line 17  Total itemized deductions", s.line_17_total_itemized))
            if s.used_itemized:
                a("  >> Itemizing (exceeds standard deduction)")
            else:
                a("  >> Using standard deduction (exceeds itemized)")

        if self.fed.schedule_b:
            s = self.fed.schedule_b
            a("")
            a("SCHEDULE B: INTEREST AND DIVIDENDS")
            a("-" * 48)
            for item in s.interest_items:
                a(f"    {item.payer_name}: {_fmt(item.amount)}")
            a(_line("Total interest", s.line_4_total_interest))
            for item in s.dividend_items:
                a(f"    {item.payer_name}: {_fmt(item.amount)}")
            a(_line("Total dividends", s.line_6_total_dividends))

        if self.fed.schedule_d:
            s = self.fed.schedule_d
            a("")
            a("SCHEDULE D: CAPITAL GAINS AND LOSSES")
            a("-" * 48)
            a(_line("Line 7   Net short-term", s.line_7_net_short_term))
            a(_line("Line 11  Cap gain distributions", s.line_11_capital_gain_distributions))
            a(_line("Line 15  Net long-term", s.line_15_net_long_term))
            a(_line("Line 16  Combined", s.line_16_combine))
            a(_line("Line 21  Net gain/loss (to 1040)", s.line_21_net_capital_gain_loss))

        if self.fed.schedule_se:
            s = self.fed.schedule_se
            a("")
            a("SCHEDULE SE: SELF-EMPLOYMENT TAX")
            a("-" * 48)
            a(_line("Line 2   Net SE earnings", s.line_2_net_se_earnings))
            a(_line("Line 3   92.35% of line 2", s.line_3_92_35_pct))
            a(_line("Line 4a  SS portion", s.line_4a_ss_portion))
            a(_line("Line 4b  Medicare portion", s.line_4b_medicare_portion))
            a(_line("Line 12  Total SE tax", s.line_12_se_tax))
            a(_line("Line 13  Deductible half", s.line_13_deductible_half))

        # ── California Form 540 ──
        a("")
        a("SECTION 7: CALIFORNIA FORM 540")
        a("-" * 48)
        a(_line("Line 13  Federal AGI", self.ca.federal_agi))
        a(_line("Line 14  CA additions", self.ca.ca_additions))
        a(_line("Line 15  CA subtractions", self.ca.ca_subtractions))
        a(_line("Line 17  CA AGI", self.ca.ca_agi))
        if self.ca.ca_used_itemized:
            a(_line("Line 18  CA itemized deduction", self.ca.ca_itemized_deduction))
        else:
            a(_line("Line 18  CA standard deduction", self.ca.ca_standard_deduction))
        a(_line("Line 19  CA taxable income", self.ca.ca_taxable_income))
        a(_line("Line 31  Tax", self.ca.ca_tax))
        a(_line("Line 32  Exemption credit", self.ca.ca_exemption_credit))
        a(_line("Line 35  Tax after exemption", self.ca.ca_tax_after_exemption))
        if self.ca.mental_health_surcharge:
            a(_line("Line 36  Mental health surcharge", self.ca.mental_health_surcharge))
        a(_line("Total CA tax", self.ca.total_ca_tax))
        a("")
        a(_line("Line 71  CA tax withheld", self.ca.ca_tax_withheld))
        a(_line("Line 74  SDI withheld", self.ca.ca_sdi_withheld))
        a(_line("Total CA payments", self.ca.total_payments))
        a("")
        if self.ca.refund > 0:
            a(_line("CA REFUND", self.ca.refund))
        elif self.ca.amount_owed > 0:
            a(_line("CA AMOUNT OWED", self.ca.amount_owed))
        else:
            a("  No refund or amount owed (break even)")

        # ── Summary ──
        a("")
        a("=" * 64)
        a("TAX RETURN SUMMARY")
        a("=" * 64)
        if self.fed.line_35a_refund > 0:
            a(f"  Federal refund:     {_fmt(self.fed.line_35a_refund)}")
        else:
            a(f"  Federal owed:       {_fmt(self.fed.line_37_amount_owed)}")
        if self.ca.refund > 0:
            a(f"  California refund:  {_fmt(self.ca.refund)}")
        else:
            a(f"  California owed:    {_fmt(self.ca.amount_owed)}")

        total = self.fed.line_35a_refund + self.ca.refund - self.fed.line_37_amount_owed - self.ca.amount_owed
        if total >= 0:
            a(f"  TOTAL REFUND:       {_fmt(total)}")
        else:
            a(f"  TOTAL OWED:         {_fmt(abs(total))}")
        a("=" * 64)

        output = Path(output_path)
        output.write_text("\n".join(lines), encoding="utf-8")
        return output

    def generate_pdf(self, output_path: str | Path) -> Path:
        """Generate PDF report from the text report content."""
        # Generate text first, then render it in PDF
        text_content = []
        text_path = Path(output_path).with_suffix(".txt")
        self.generate_text(text_path)
        text_content = text_path.read_text(encoding="utf-8").splitlines()

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Courier", size=9)

        for line in text_content:
            pdf.cell(0, 4, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        output = Path(output_path)
        pdf.output(str(output))
        return output
