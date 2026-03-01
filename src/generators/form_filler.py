"""Fill official IRS and California FTB PDF forms with computed tax data."""

from __future__ import annotations

import copy
from decimal import Decimal
from pathlib import Path
from typing import Optional

from pypdf import PdfReader, PdfWriter

from src.models import (
    BasisReportedToIRS,
    TaxReturn,
    TermType,
)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def _amt(value: Decimal) -> str:
    """Format amount for IRS form field (whole dollars, no commas)."""
    rounded = int(round(value))
    if rounded < 0:
        return f"({abs(rounded)})"
    return str(rounded) if rounded != 0 else ""


def _amt_always(value: Decimal) -> str:
    """Format amount always showing value, even zero."""
    rounded = int(round(value))
    if rounded < 0:
        return f"({abs(rounded)})"
    return str(rounded)


def _cents(value: Decimal) -> str:
    """Format amount with cents for fields that need them."""
    if value == 0:
        return ""
    return f"{float(value):.2f}"


class IRSFormFiller:
    """Fills official IRS PDF forms with computed tax data."""

    def __init__(self, tax_return: TaxReturn):
        self.tr = tax_return
        self.fed = tax_return.federal
        self.ca = tax_return.california
        self.inp = tax_return.input_data

    def generate_all(self, output_dir: Path) -> list[Path]:
        """Generate all applicable filled PDF forms."""
        output_dir.mkdir(exist_ok=True)
        generated = []

        # Form 1040
        path = self._fill_form_1040(output_dir / "Form_1040.pdf")
        if path:
            generated.append(path)

        # Schedule 1 (additional income / adjustments)
        if self.fed.schedule_1:
            path = self._fill_schedule_1(output_dir / "Schedule_1.pdf")
            if path:
                generated.append(path)

        # Schedule B (if interest > $1,500 or dividends > $1,500)
        if self.fed.schedule_b:
            path = self._fill_schedule_b(output_dir / "Schedule_B.pdf")
            if path:
                generated.append(path)

        # Schedule D (if capital gains/losses)
        if self.fed.schedule_d:
            path = self._fill_schedule_d(output_dir / "Schedule_D.pdf")
            if path:
                generated.append(path)

        # Form 8949 (individual transactions)
        if self.fed.schedule_d:
            paths = self._fill_form_8949(output_dir)
            generated.extend(paths)

        # Schedule 2 (additional taxes)
        if self.fed.schedule_2 and self.fed.schedule_2.line_21_total_additional_taxes > 0:
            path = self._fill_schedule_2(output_dir / "Schedule_2.pdf")
            if path:
                generated.append(path)

        # California Form 540
        path = self._fill_ca_540(output_dir / "CA_Form_540.pdf")
        if path:
            generated.append(path)

        return generated

    def _fill_form_1040(self, output_path: Path) -> Optional[Path]:
        """Fill Form 1040."""
        template = TEMPLATES_DIR / "f1040.pdf"
        if not template.exists():
            return None

        reader = PdfReader(str(template))
        writer = PdfWriter()
        writer.append(reader)

        p1 = "topmostSubform[0].Page1[0]"
        p2 = "topmostSubform[0].Page2[0]"
        addr = f"{p1}.Address_ReadOrder[0]"

        filing_status_map = {
            "single": "/1",
            "married_filing_jointly": "/2",
            "married_filing_separately": "/3",
            "head_of_household": "/4",
            "qualifying_surviving_spouse": "/5",
        }

        fields = {}

        # --- Header ---
        fields[f"{p1}.f1_14[0]"] = f"{self.inp.first_name}"
        fields[f"{p1}.f1_15[0]"] = self.inp.last_name
        ssn = self.inp.ssn.replace("-", "")
        fields[f"{p1}.f1_16[0]"] = ssn

        # Spouse (MFJ)
        if self.inp.filing_status == "married_filing_jointly" and self.inp.spouse_first_name:
            fields[f"{p1}.f1_17[0]"] = self.inp.spouse_first_name
            fields[f"{p1}.f1_18[0]"] = self.inp.spouse_last_name or ""
            if self.inp.spouse_ssn:
                sp_ssn = self.inp.spouse_ssn.replace("-", "")
                fields[f"{p1}.f1_19[0]"] = sp_ssn

        # Address
        if self.inp.address:
            fields[f"{addr}.f1_20[0]"] = self.inp.address
        if self.inp.city:
            fields[f"{addr}.f1_22[0]"] = self.inp.city
        if self.inp.state:
            fields[f"{addr}.f1_23[0]"] = self.inp.state
        if self.inp.zip_code:
            fields[f"{addr}.f1_24[0]"] = self.inp.zip_code

        # --- Page 1: Income ---
        fields[f"{p1}.f1_47[0]"] = _amt(self.fed.line_1a_wages)          # Line 1a
        fields[f"{p1}.f1_57[0]"] = _amt(self.fed.line_1a_wages)          # Line 1z
        fields[f"{p1}.f1_58[0]"] = _amt(self.fed.line_2a_tax_exempt_interest)  # Line 2a
        fields[f"{p1}.f1_59[0]"] = _amt(self.fed.line_2b_taxable_interest)     # Line 2b
        fields[f"{p1}.f1_60[0]"] = _amt(self.fed.line_3a_qualified_dividends)  # Line 3a
        fields[f"{p1}.f1_61[0]"] = _amt(self.fed.line_3b_ordinary_dividends)   # Line 3b
        # Lines 4a/4b (IRA) - skip if zero
        # Lines 5a/5b (Pensions) - skip if zero
        # Lines 6a/6b (Social Security) - skip if zero
        fields[f"{p1}.f1_70[0]"] = _amt(self.fed.line_7_capital_gain_loss)     # Line 7
        fields[f"{p1}.f1_72[0]"] = _amt(self.fed.line_8_other_income)          # Line 8
        fields[f"{p1}.f1_73[0]"] = _amt(self.fed.line_9_total_income)          # Line 9
        fields[f"{p1}.f1_74[0]"] = _amt(self.fed.line_10_adjustments)          # Line 10
        fields[f"{p1}.f1_75[0]"] = _amt(self.fed.line_11_adjusted_gross_income)  # Line 11

        # --- Page 2: Tax and Credits ---
        fields[f"{p2}.f2_01[0]"] = _amt(self.fed.line_11_adjusted_gross_income)  # Line 11b
        fields[f"{p2}.f2_02[0]"] = _amt(self.fed.line_12_standard_deduction)     # Line 12e
        fields[f"{p2}.f2_03[0]"] = _amt(self.fed.line_13_qualified_business_deduction)  # Line 13a
        fields[f"{p2}.f2_05[0]"] = _amt(self.fed.line_14_total_deductions)       # Line 14
        fields[f"{p2}.f2_06[0]"] = _amt(self.fed.line_15_taxable_income)         # Line 15
        fields[f"{p2}.f2_08[0]"] = _amt(self.fed.line_16_tax)                    # Line 16
        fields[f"{p2}.f2_09[0]"] = _amt(self.fed.line_17_schedule_2_part1)       # Line 17
        fields[f"{p2}.f2_10[0]"] = _amt(self.fed.line_18_sum)                    # Line 18
        fields[f"{p2}.f2_11[0]"] = _amt(self.fed.line_19_child_credit)           # Line 19
        fields[f"{p2}.f2_12[0]"] = _amt(self.fed.line_20_schedule_3_part1)       # Line 20
        fields[f"{p2}.f2_13[0]"] = _amt(self.fed.line_21_total_credits)          # Line 21
        fields[f"{p2}.f2_14[0]"] = _amt(self.fed.line_22_after_credits)          # Line 22
        fields[f"{p2}.f2_15[0]"] = _amt(self.fed.line_23_other_taxes)            # Line 23
        fields[f"{p2}.f2_16[0]"] = _amt(self.fed.line_24_total_tax)              # Line 24

        # --- Page 2: Payments ---
        fields[f"{p2}.f2_17[0]"] = _amt(self.fed.line_25a_w2_withheld)           # Line 25a
        fields[f"{p2}.f2_18[0]"] = _amt(self.fed.line_25b_1099_withheld)         # Line 25b
        fields[f"{p2}.f2_20[0]"] = _amt(self.fed.line_25d_total_withheld)        # Line 25d
        fields[f"{p2}.f2_29[0]"] = _amt(self.fed.line_33_total_payments)         # Line 33

        # --- Page 2: Refund or Amount Owed ---
        if self.fed.line_34_overpayment > 0:
            fields[f"{p2}.f2_30[0]"] = _amt(self.fed.line_34_overpayment)    # Line 34
            fields[f"{p2}.f2_31[0]"] = _amt(self.fed.line_35a_refund)        # Line 35a
        if self.fed.line_37_amount_owed > 0:
            fields[f"{p2}.f2_35[0]"] = _amt(self.fed.line_37_amount_owed)    # Line 37

        # Write fields to all pages
        for page in writer.pages:
            writer.update_page_form_field_values(page, fields)

        # Set filing status checkbox
        fs_value = filing_status_map.get(self.inp.filing_status, "/1")
        self._set_checkbox(writer, "topmostSubform[0].Page1[0].c1_8[0]", fs_value)

        with open(output_path, "wb") as f:
            writer.write(f)
        return output_path

    def _fill_schedule_1(self, output_path: Path) -> Optional[Path]:
        """Fill Schedule 1 (Additional Income and Adjustments to Income)."""
        template = TEMPLATES_DIR / "f1040s1.pdf"
        if not template.exists() or not self.fed.schedule_1:
            return None

        s1 = self.fed.schedule_1
        reader = PdfReader(str(template))
        writer = PdfWriter()
        writer.append(reader)

        p1 = "topmostSubform[0].Page1[0]"
        p2 = "topmostSubform[0].Page2[0]"
        fields = {}

        # Header
        fields[f"{p1}.f1_01[0]"] = f"{self.inp.first_name} {self.inp.last_name}"
        ssn = self.inp.ssn.replace("-", "")
        fields[f"{p1}.f1_02[0]"] = ssn

        # Part I - Additional Income
        if s1.line_3_business_income:
            fields[f"{p1}.f1_04[0]"] = _amt(s1.line_3_business_income)   # Line 3
        if s1.line_5_rental_income:
            fields[f"{p1}.f1_06[0]"] = _amt(s1.line_5_rental_income)     # Line 5
        if s1.line_8a_other_income:
            fields[f"{p1}.f1_09[0]"] = _amt(s1.line_8a_other_income)     # Line 8a
        fields[f"{p1}.f1_12[0]"] = _amt(s1.line_10_total_additional_income)  # Line 10

        # Part II - Adjustments to Income
        if s1.line_15_se_tax_deduction:
            fields[f"{p2}.f2_04[0]"] = _amt(s1.line_15_se_tax_deduction)  # Line 15
        if s1.line_18_early_withdrawal_penalty:
            fields[f"{p2}.f2_07[0]"] = _amt(s1.line_18_early_withdrawal_penalty)  # Line 18
        if s1.line_21_student_loan_interest:
            fields[f"{p2}.f2_10[0]"] = _amt(s1.line_21_student_loan_interest)  # Line 21
        fields[f"{p2}.f2_14[0]"] = _amt(s1.line_26_total_adjustments)    # Line 26

        for page in writer.pages:
            writer.update_page_form_field_values(page, fields)

        with open(output_path, "wb") as f:
            writer.write(f)
        return output_path

    def _fill_schedule_b(self, output_path: Path) -> Optional[Path]:
        """Fill Schedule B (Interest and Ordinary Dividends)."""
        template = TEMPLATES_DIR / "f1040sb.pdf"
        if not template.exists() or not self.fed.schedule_b:
            return None

        sb = self.fed.schedule_b
        reader = PdfReader(str(template))
        writer = PdfWriter()
        writer.append(reader)

        p1 = "topmostSubform[0].Page1[0]"
        fields = {}

        # Header
        fields[f"{p1}.f1_01[0]"] = f"{self.inp.first_name} {self.inp.last_name}"
        ssn = self.inp.ssn.replace("-", "")
        fields[f"{p1}.f1_02[0]"] = ssn

        # Part I - Interest (up to 14 payers)
        # Fields are pairs: f1_03/f1_04 = row 1 name/amount, f1_05/f1_06 = row 2, etc.
        interest_fields_start = 3
        for i, item in enumerate(sb.interest_items[:14]):
            name_idx = interest_fields_start + (i * 2)
            amt_idx = name_idx + 1
            fields[f"{p1}.f1_{name_idx:02d}[0]"] = item.payer_name
            fields[f"{p1}.f1_{amt_idx:02d}[0]"] = _amt(item.amount)

        # Line 2 - Sum of interest, Line 4 - Total interest
        fields[f"{p1}.f1_31[0]"] = _amt(sb.line_4_total_interest)
        fields[f"{p1}.f1_33[0]"] = _amt(sb.line_4_total_interest)

        # Part II - Dividends (up to 14 payers)
        # f1_34/f1_35 = row 1 name/amount, f1_36/f1_37 = row 2, etc.
        div_fields_start = 34
        for i, item in enumerate(sb.dividend_items[:14]):
            name_idx = div_fields_start + (i * 2)
            amt_idx = name_idx + 1
            fields[f"{p1}.f1_{name_idx:02d}[0]"] = item.payer_name
            fields[f"{p1}.f1_{amt_idx:02d}[0]"] = _amt(item.amount)

        # Line 6 - Total dividends
        fields[f"{p1}.f1_64[0]"] = _amt(sb.line_6_total_dividends)

        for page in writer.pages:
            writer.update_page_form_field_values(page, fields)

        with open(output_path, "wb") as f:
            writer.write(f)
        return output_path

    def _fill_schedule_d(self, output_path: Path) -> Optional[Path]:
        """Fill Schedule D (Capital Gains and Losses)."""
        template = TEMPLATES_DIR / "f1040sd.pdf"
        if not template.exists() or not self.fed.schedule_d:
            return None

        sd = self.fed.schedule_d
        reader = PdfReader(str(template))
        writer = PdfWriter()
        writer.append(reader)

        p1 = "topmostSubform[0].Page1[0]"
        p2 = "topmostSubform[0].Page2[0]"
        fields = {}

        # Header
        fields[f"{p1}.f1_1[0]"] = f"{self.inp.first_name} {self.inp.last_name}"
        ssn = self.inp.ssn.replace("-", "")
        fields[f"{p1}.f1_2[0]"] = ssn

        # Part I - Short-Term (summary lines)
        # Line 1a row: proceeds, cost, adjustments, gain/loss
        # Schedule D rows are in Table_PartI: Row1a, Row1b, Row2, Row3
        # Row1a = Line 1a (ST basis reported) - 4 columns: proceeds, cost, adj, gain
        st_reported = sd.line_1a_short_term_basis_reported
        st_not_reported = sd.line_1b_short_term_basis_not_reported

        # Line 7 - Net short-term capital gain or (loss)
        fields[f"{p1}.f1_22[0]"] = _amt(sd.line_7_net_short_term)  # Line 7

        # Part II - Long-Term
        # Line 15 - Net long-term
        fields[f"{p1}.f1_43[0]"] = _amt(sd.line_15_net_long_term)  # Line 15

        # Part III - Summary (Page 2)
        fields[f"{p2}.f2_1[0]"] = _amt(sd.line_16_combine)  # Line 16
        fields[f"{p2}.f2_4[0]"] = _amt(sd.line_21_net_capital_gain_loss)  # Line 21

        for page in writer.pages:
            writer.update_page_form_field_values(page, fields)

        with open(output_path, "wb") as f:
            writer.write(f)
        return output_path

    def _fill_form_8949(self, output_dir: Path) -> list[Path]:
        """Fill Form 8949 (Sales and Other Dispositions of Capital Assets).

        May generate multiple pages if there are many transactions.
        Returns list of generated file paths.
        """
        template = TEMPLATES_DIR / "f8949.pdf"
        if not template.exists():
            return []

        # Categorize transactions
        st_covered = []  # Short-term, basis reported (Box A)
        st_noncovered = []  # Short-term, basis not reported (Box B)
        lt_covered = []  # Long-term, basis reported (Box D)
        lt_noncovered = []  # Long-term, basis not reported (Box E)

        for b in self.inp.forms_1099_b:
            for t in b.transactions:
                is_short = t.term == TermType.SHORT_TERM
                is_covered = t.basis_reported_to_irs == BasisReportedToIRS.YES

                if is_short and is_covered:
                    st_covered.append(t)
                elif is_short and not is_covered:
                    st_noncovered.append(t)
                elif not is_short and is_covered:
                    lt_covered.append(t)
                else:
                    lt_noncovered.append(t)

        generated = []
        categories = [
            ("A", st_covered, "8949_Part1_BoxA.pdf"),
            ("B", st_noncovered, "8949_Part1_BoxB.pdf"),
            ("D", lt_covered, "8949_Part2_BoxD.pdf"),
            ("E", lt_noncovered, "8949_Part2_BoxE.pdf"),
        ]

        for box, transactions, filename in categories:
            if not transactions:
                continue
            path = self._fill_8949_page(
                template, output_dir / filename, box, transactions
            )
            if path:
                generated.append(path)

        return generated

    def _fill_8949_page(
        self,
        template: Path,
        output_path: Path,
        box: str,
        transactions: list,
    ) -> Optional[Path]:
        """Fill one Form 8949 page for a specific box category."""
        reader = PdfReader(str(template))
        writer = PdfWriter()
        writer.append(reader)

        # Determine which page to use (Part I = page 1 for ST, Part II = page 2 for LT)
        is_part1 = box in ("A", "B", "C")  # Short-term
        page_prefix = "topmostSubform[0].Page1[0]" if is_part1 else "topmostSubform[0].Page2[0]"
        field_prefix = "f1" if is_part1 else "f2"

        fields = {}

        # Header
        fields[f"{page_prefix}.{field_prefix}_01[0]"] = (
            f"{self.inp.first_name} {self.inp.last_name}"
        )
        ssn = self.inp.ssn.replace("-", "")
        fields[f"{page_prefix}.{field_prefix}_02[0]"] = (
            ssn
        )

        # Set checkbox for box type
        # Box A/D = basis reported, B/E = basis not reported
        checkbox_map = {"A": 0, "B": 1, "C": 2, "D": 0, "E": 1, "F": 2}
        cb_idx = checkbox_map.get(box, 0)
        cb_name = f"{page_prefix}.c{'1' if is_part1 else '2'}_1[{cb_idx}]"

        # Fill transaction rows (up to 11 per page)
        # Each row has 8 fields: description, date_acquired, date_sold,
        # proceeds, cost_basis, adjustment_code, adjustment_amount, gain_loss
        rows_per_page = 11
        table_prefix = f"{page_prefix}.Table_Line1_Part{'1' if is_part1 else '2'}[0]"

        totals_proceeds = Decimal("0")
        totals_cost = Decimal("0")
        totals_adj = Decimal("0")
        totals_gain = Decimal("0")

        for i, txn in enumerate(transactions[:rows_per_page]):
            row_num = i + 1
            row = f"{table_prefix}.Row{row_num}[0]"
            base_idx = 3 + (i * 8) if is_part1 else 3 + (i * 8)
            fp = field_prefix

            fields[f"{row}.{fp}_{base_idx:02d}[0]"] = txn.description[:30]
            fields[f"{row}.{fp}_{base_idx+1:02d}[0]"] = txn.date_acquired or "VARIOUS"
            fields[f"{row}.{fp}_{base_idx+2:02d}[0]"] = txn.date_sold or ""
            fields[f"{row}.{fp}_{base_idx+3:02d}[0]"] = _amt(txn.proceeds)
            fields[f"{row}.{fp}_{base_idx+4:02d}[0]"] = _amt(txn.cost_basis)

            adj_code = ""
            adj_amount = Decimal("0")
            if txn.wash_sale_loss_disallowed > 0:
                adj_code = "W"
                adj_amount = txn.wash_sale_loss_disallowed

            fields[f"{row}.{fp}_{base_idx+5:02d}[0]"] = adj_code
            fields[f"{row}.{fp}_{base_idx+6:02d}[0]"] = _amt(adj_amount) if adj_amount else ""
            fields[f"{row}.{fp}_{base_idx+7:02d}[0]"] = _amt(txn.gain_or_loss or Decimal("0"))

            totals_proceeds += txn.proceeds
            totals_cost += txn.cost_basis
            totals_adj += adj_amount
            totals_gain += txn.gain_or_loss or Decimal("0")

        # Totals row
        totals_row_num = rows_per_page + 1  # Row 12 for totals (Row11 is last data)
        totals_base = 3 + (rows_per_page * 8)
        totals_row = f"{table_prefix}.Row{totals_row_num}[0]"

        # Summary fields at the bottom
        fp = field_prefix
        fields[f"{page_prefix}.{fp}_91[0]"] = _amt(totals_proceeds)
        fields[f"{page_prefix}.{fp}_92[0]"] = _amt(totals_cost)
        fields[f"{page_prefix}.{fp}_93[0]"] = _amt(totals_adj) if totals_adj else ""
        fields[f"{page_prefix}.{fp}_94[0]"] = _amt(totals_gain)

        for page in writer.pages:
            writer.update_page_form_field_values(page, fields)

        # Set checkbox
        self._set_checkbox(writer, cb_name, "/1")

        with open(output_path, "wb") as f:
            writer.write(f)
        return output_path

    def _fill_schedule_2(self, output_path: Path) -> Optional[Path]:
        """Fill Schedule 2 (Additional Taxes)."""
        template = TEMPLATES_DIR / "f1040s2.pdf"
        if not template.exists() or not self.fed.schedule_2:
            return None

        s2 = self.fed.schedule_2
        reader = PdfReader(str(template))
        writer = PdfWriter()
        writer.append(reader)

        fields = {}
        p1 = "form1[0].Page1[0]"
        p2 = "form1[0].Page2[0]"

        # Header
        fields[f"{p1}.f1_01[0]"] = f"{self.inp.first_name} {self.inp.last_name}"
        ssn = self.inp.ssn.replace("-", "")
        fields[f"{p1}.f1_02[0]"] = ssn

        # Part II - Other Taxes (Lines 4-12 are on Page1)
        # Line 4 - SE tax
        if s2.line_6_se_tax > 0:
            fields[f"{p1}.f1_15[0]"] = _amt(s2.line_6_se_tax)
        # Line 11 - Additional Medicare Tax
        if s2.line_11_additional_medicare > 0:
            fields[f"{p1}.f1_22[0]"] = _amt(s2.line_11_additional_medicare)
        # Line 12 - Net Investment Income Tax
        if s2.line_17_niit > 0:
            fields[f"{p1}.f1_23[0]"] = _amt(s2.line_17_niit)
        # Line 21 - Total other taxes
        fields[f"{p2}.f2_24[0]"] = _amt(s2.line_21_total_additional_taxes)

        for page in writer.pages:
            writer.update_page_form_field_values(page, fields)

        with open(output_path, "wb") as f:
            writer.write(f)
        return output_path

    def _fill_ca_540(self, output_path: Path) -> Optional[Path]:
        """Fill California Form 540."""
        template = TEMPLATES_DIR / "ca540.pdf"
        if not template.exists():
            return None

        reader = PdfReader(str(template))
        writer = PdfWriter()
        writer.append(reader)

        ca = self.ca
        fields = {}

        # CA 540 uses field names like "540_form_NNNN"
        # Page 1 header - from tooltips
        fields["540_form_1003"] = self.inp.first_name        # First name
        fields["540_form_1005"] = self.inp.last_name          # Last name
        ssn = self.inp.ssn.replace("-", "")
        fields["540_form_1007"] = ssn  # SSN

        # Spouse (MFJ)
        if self.inp.filing_status == "married_filing_jointly" and self.inp.spouse_first_name:
            fields["540_form_1004"] = self.inp.spouse_first_name   # Spouse first name
            fields["540_form_1006"] = self.inp.spouse_last_name or ""  # Spouse last name
            if self.inp.spouse_ssn:
                sp_ssn = self.inp.spouse_ssn.replace("-", "")
                fields["540_form_1008"] = sp_ssn

        # Address
        if self.inp.address:
            fields["540_form_1015"] = self.inp.address
        if self.inp.city:
            fields["540_form_1018"] = self.inp.city
        if self.inp.state:
            fields["540_form_1019"] = self.inp.state
        if self.inp.zip_code:
            fields["540_form_1020"] = self.inp.zip_code

        # Filing status radio button
        # 540_form_1036 RB: /1=Single, /2=MFJ, /3=MFS, /4=HOH, /5=QSS

        # Exemptions (Line 7)
        is_mfj = self.inp.filing_status == "married_filing_jointly"
        num_exemptions = "2" if is_mfj else "1"
        fields["540_form_1041"] = num_exemptions               # Line 7 - number of exemptions
        fields["540_form_1042"] = _amt(ca.ca_exemption_credit)  # Line 7 amount

        # Exemption total (Line 11)
        fields["540_form_2017"] = _amt(ca.ca_exemption_credit)  # Line 11

        # Income
        # Line 12 - State wages from W-2 Box 16
        total_state_wages = sum(w.state_wages for w in self.inp.w2s)
        fields["540_form_2018"] = _amt(total_state_wages)       # Line 12

        fields["540_form_2019"] = _amt(ca.federal_agi)          # Line 13 - Federal AGI
        fields["540_form_2020"] = _amt(ca.ca_subtractions)      # Line 14 - Subtractions
        # Line 15 = Line 13 - Line 14
        line_15 = ca.federal_agi - ca.ca_subtractions
        fields["540_form_2021"] = _amt(line_15)                 # Line 15
        fields["540_form_2022"] = _amt(ca.ca_additions)         # Line 16 - Additions
        fields["540_form_2023"] = _amt(ca.ca_agi)               # Line 17 - CA AGI
        fields["540_form_2024"] = _amt(ca.ca_standard_deduction)  # Line 18
        fields["540_form_2025"] = _amt(ca.ca_taxable_income)    # Line 19

        # Tax
        fields["540_form_2030"] = _amt(ca.ca_tax)               # Line 31
        fields["540_form_2031"] = _amt(ca.ca_exemption_credit)  # Line 32
        fields["540_form_2032"] = _amt(ca.ca_tax_after_exemption)  # Line 33

        # Line 35 - Total tax (after exemption + mental health surcharge)
        fields["540_form_2036"] = _amt(ca.total_ca_tax)         # Line 35

        # Line 48 (subtract credits from tax) - same as total tax if no credits
        fields["540_form_3006"] = _amt(ca.total_ca_tax)         # Line 48
        fields["540_form_3010"] = _amt(ca.total_ca_tax)         # Line 64 - Total tax

        # Payments
        fields["540_form_3011"] = _amt(ca.ca_tax_withheld)      # Line 71
        if ca.ca_sdi_withheld > 0:
            fields["540_form_3014"] = _amt(ca.ca_sdi_withheld)  # Line 74 - Excess SDI/VPDI
        fields["540_form_3018"] = _amt(ca.total_payments)       # Line 78 - Total payments

        # Result
        if ca.refund > 0:
            fields["540_form_3023"] = _amt(ca.total_payments - ca.total_ca_tax)  # Line 93
            fields["540_form_3025"] = _amt(ca.refund)           # Line 95
        elif ca.amount_owed > 0:
            fields["540_form_3024"] = _amt(ca.amount_owed)      # Line 94

        for page in writer.pages:
            writer.update_page_form_field_values(page, fields)

        # Set filing status
        ca_fs_map = {
            "single": "/1",
            "married_filing_jointly": "/2",
            "married_filing_separately": "/3",
            "head_of_household": "/4",
            "qualifying_surviving_spouse": "/5",
        }
        ca_fs_value = ca_fs_map.get(self.inp.filing_status, "/1")
        self._set_checkbox(writer, "540_form_1036 RB", ca_fs_value)

        with open(output_path, "wb") as f:
            writer.write(f)
        return output_path

    @staticmethod
    def _set_checkbox(writer: PdfWriter, field_name: str, value: str) -> None:
        """Set a checkbox/radio button value in the PDF."""
        for page in writer.pages:
            if "/Annots" not in page:
                continue
            for annot in page["/Annots"]:
                obj = annot.get_object()
                if "/T" in obj and str(obj["/T"]) == field_name.split(".")[-1].split("[")[0]:
                    # Try to match the full path or just the field name
                    pass
        # Use the writer's built-in method
        try:
            writer.update_page_form_field_values(
                writer.pages[0], {field_name: value}
            )
        except Exception:
            pass
