"""Pydantic data models for all tax input documents and computation results."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# =============================================
# W-2 Models
# =============================================

class W2Box12(BaseModel):
    code: str
    amount: Decimal


class W2Box14(BaseModel):
    description: str
    amount: Decimal


class W2(BaseModel):
    """IRS Form W-2: Wage and Tax Statement."""
    employer_ein: str = Field(description="Box b")
    employer_name: str = Field(description="Box c")
    employer_address: Optional[str] = None
    employee_ssn: str = Field(description="Box a")
    employee_name: str = Field(description="Box e")
    employee_address: Optional[str] = None

    wages_tips_other_comp: Decimal = Field(description="Box 1")
    federal_income_tax_withheld: Decimal = Field(description="Box 2")
    social_security_wages: Decimal = Field(description="Box 3")
    social_security_tax_withheld: Decimal = Field(description="Box 4")
    medicare_wages_and_tips: Decimal = Field(description="Box 5")
    medicare_tax_withheld: Decimal = Field(description="Box 6")
    social_security_tips: Decimal = Field(default=Decimal("0"), description="Box 7")
    allocated_tips: Decimal = Field(default=Decimal("0"), description="Box 8")
    dependent_care_benefits: Decimal = Field(default=Decimal("0"), description="Box 10")
    nonqualified_plans: Decimal = Field(default=Decimal("0"), description="Box 11")
    box_12_codes: list[W2Box12] = Field(default_factory=list, description="Box 12a-d")
    statutory_employee: bool = Field(default=False, description="Box 13")
    retirement_plan: bool = Field(default=False, description="Box 13")
    third_party_sick_pay: bool = Field(default=False, description="Box 13")
    box_14_other: list[W2Box14] = Field(default_factory=list, description="Box 14")

    state: Optional[str] = Field(default=None, description="Box 15")
    state_employer_id: Optional[str] = Field(default=None, description="Box 15")
    state_wages: Decimal = Field(default=Decimal("0"), description="Box 16")
    state_income_tax: Decimal = Field(default=Decimal("0"), description="Box 17")
    local_wages: Decimal = Field(default=Decimal("0"), description="Box 18")
    local_income_tax: Decimal = Field(default=Decimal("0"), description="Box 19")
    locality_name: Optional[str] = Field(default=None, description="Box 20")


# =============================================
# 1099 Models
# =============================================

class Form1099INT(BaseModel):
    """Form 1099-INT: Interest Income."""
    payer_name: str
    payer_tin: Optional[str] = None
    recipient_name: str
    recipient_tin: str

    box_1_interest_income: Decimal = Field(default=Decimal("0"))
    box_2_early_withdrawal_penalty: Decimal = Field(default=Decimal("0"))
    box_3_us_savings_bond_interest: Decimal = Field(default=Decimal("0"))
    box_4_federal_tax_withheld: Decimal = Field(default=Decimal("0"))
    box_5_investment_expenses: Decimal = Field(default=Decimal("0"))
    box_6_foreign_tax_paid: Decimal = Field(default=Decimal("0"))
    box_7_foreign_country: Optional[str] = None
    box_8_tax_exempt_interest: Decimal = Field(default=Decimal("0"))
    box_9_private_activity_bond: Decimal = Field(default=Decimal("0"))
    box_10_market_discount: Decimal = Field(default=Decimal("0"))
    box_11_bond_premium: Decimal = Field(default=Decimal("0"))
    box_12_bond_premium_treasury: Decimal = Field(default=Decimal("0"))
    box_13_bond_premium_tax_exempt: Decimal = Field(default=Decimal("0"))
    state: Optional[str] = None
    state_id: Optional[str] = None
    state_tax_withheld: Decimal = Field(default=Decimal("0"))


class Form1099DIV(BaseModel):
    """Form 1099-DIV: Dividends and Distributions."""
    payer_name: str
    payer_tin: Optional[str] = None
    recipient_name: str
    recipient_tin: str

    box_1a_ordinary_dividends: Decimal = Field(default=Decimal("0"))
    box_1b_qualified_dividends: Decimal = Field(default=Decimal("0"))
    box_2a_total_capital_gain: Decimal = Field(default=Decimal("0"))
    box_2b_unrecaptured_1250_gain: Decimal = Field(default=Decimal("0"))
    box_2c_section_1202_gain: Decimal = Field(default=Decimal("0"))
    box_2d_collectibles_gain: Decimal = Field(default=Decimal("0"))
    box_2e_section_897_ordinary: Decimal = Field(default=Decimal("0"))
    box_2f_section_897_capital_gain: Decimal = Field(default=Decimal("0"))
    box_3_nondividend_distributions: Decimal = Field(default=Decimal("0"))
    box_4_federal_tax_withheld: Decimal = Field(default=Decimal("0"))
    box_5_section_199a_dividends: Decimal = Field(default=Decimal("0"))
    box_6_investment_expenses: Decimal = Field(default=Decimal("0"))
    box_7_foreign_tax_paid: Decimal = Field(default=Decimal("0"))
    box_8_foreign_country: Optional[str] = None
    box_9_cash_liquidation: Decimal = Field(default=Decimal("0"))
    box_10_noncash_liquidation: Decimal = Field(default=Decimal("0"))
    box_11_exempt_interest_dividends: Decimal = Field(default=Decimal("0"))
    box_12_private_activity_bond: Decimal = Field(default=Decimal("0"))
    state: Optional[str] = None
    state_id: Optional[str] = None
    state_tax_withheld: Decimal = Field(default=Decimal("0"))


class Form1099NEC(BaseModel):
    """Form 1099-NEC: Nonemployee Compensation."""
    payer_name: str
    payer_tin: Optional[str] = None
    recipient_name: str
    recipient_tin: str

    box_1_nonemployee_compensation: Decimal = Field(description="Box 1")
    box_2_payer_direct_sales: bool = Field(default=False)
    box_4_federal_tax_withheld: Decimal = Field(default=Decimal("0"))
    state: Optional[str] = None
    state_id: Optional[str] = None
    state_income_tax_withheld: Decimal = Field(default=Decimal("0"))


class TermType(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    UNKNOWN = "unknown"


class BasisReportedToIRS(str, Enum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class Form1099BTransaction(BaseModel):
    """A single transaction from 1099-B."""
    description: str = Field(description="1a: Description of property")
    date_acquired: Optional[str] = Field(default=None, description="1b")
    date_sold: Optional[str] = Field(default=None, description="1c")
    proceeds: Decimal = Field(description="1d")
    cost_basis: Decimal = Field(default=Decimal("0"), description="1e")
    accrued_market_discount: Decimal = Field(default=Decimal("0"), description="1f")
    wash_sale_loss_disallowed: Decimal = Field(default=Decimal("0"), description="1g")
    gain_or_loss: Optional[Decimal] = None
    term: TermType = Field(default=TermType.UNKNOWN)
    basis_reported_to_irs: BasisReportedToIRS = Field(default=BasisReportedToIRS.UNKNOWN)
    federal_tax_withheld: Decimal = Field(default=Decimal("0"))

    @model_validator(mode="after")
    def compute_gain_loss(self) -> "Form1099BTransaction":
        if self.gain_or_loss is None:
            self.gain_or_loss = self.proceeds - self.cost_basis + self.wash_sale_loss_disallowed
        return self


class Form1099B(BaseModel):
    """Form 1099-B: Proceeds from Broker and Barter Exchange Transactions."""
    broker_name: str
    broker_tin: Optional[str] = None
    recipient_name: str
    recipient_tin: str
    transactions: list[Form1099BTransaction] = Field(default_factory=list)

    @property
    def total_proceeds(self) -> Decimal:
        return sum((t.proceeds for t in self.transactions), Decimal("0"))

    @property
    def total_cost_basis(self) -> Decimal:
        return sum((t.cost_basis for t in self.transactions), Decimal("0"))

    @property
    def total_gain_loss(self) -> Decimal:
        return sum(
            (t.gain_or_loss for t in self.transactions if t.gain_or_loss is not None),
            Decimal("0"),
        )

    @property
    def total_federal_tax_withheld(self) -> Decimal:
        return sum((t.federal_tax_withheld for t in self.transactions), Decimal("0"))


class Form1098E(BaseModel):
    """Form 1098-E: Student Loan Interest Statement."""
    lender_name: str
    lender_tin: Optional[str] = None
    borrower_name: str
    borrower_ssn: str
    box_1_student_loan_interest_paid: Decimal = Field(default=Decimal("0"))
    box_2_capitalized_interest: bool = Field(default=False)


class Form1098(BaseModel):
    """Form 1098: Mortgage Interest Statement."""
    lender_name: str
    lender_tin: Optional[str] = None
    borrower_name: str
    borrower_ssn: str
    box_1_mortgage_interest: Decimal = Field(default=Decimal("0"))
    box_2_outstanding_principal: Decimal = Field(default=Decimal("0"))
    box_5_mortgage_insurance_premiums: Decimal = Field(default=Decimal("0"))
    box_6_points_paid: Decimal = Field(default=Decimal("0"))
    box_10_property_tax: Decimal = Field(default=Decimal("0"))


class Form1099SA(BaseModel):
    """Form 1099-SA: Distributions From an HSA, Archer MSA, or Medicare Advantage MSA."""
    payer_name: str
    payer_tin: Optional[str] = None
    recipient_name: str
    recipient_tin: str

    box_1_gross_distribution: Decimal = Field(default=Decimal("0"))
    box_2_earnings_on_excess: Decimal = Field(default=Decimal("0"))
    box_3_distribution_code: str = Field(default="1", description="1=Normal, 2=Excess, 3=Disability, 4=Death, 5=Prohibited, 6=Transfer")
    box_5_account_type: str = Field(default="HSA", description="HSA, Archer MSA, or MA MSA")
    qualified: bool = Field(default=True, description="Whether distribution was used for qualified medical expenses")


class Form1099MISC(BaseModel):
    """Form 1099-MISC: Miscellaneous Information."""
    payer_name: str
    payer_tin: Optional[str] = None
    recipient_name: str
    recipient_tin: str

    box_1_rents: Decimal = Field(default=Decimal("0"))
    box_2_royalties: Decimal = Field(default=Decimal("0"))
    box_3_other_income: Decimal = Field(default=Decimal("0"))
    box_4_federal_tax_withheld: Decimal = Field(default=Decimal("0"))
    box_5_fishing_boat_proceeds: Decimal = Field(default=Decimal("0"))
    box_6_medical_payments: Decimal = Field(default=Decimal("0"))
    box_8_substitute_payments: Decimal = Field(default=Decimal("0"))
    box_9_crop_insurance: Decimal = Field(default=Decimal("0"))
    box_10_gross_proceeds_attorney: Decimal = Field(default=Decimal("0"))
    box_11_fish_purchased_for_resale: Decimal = Field(default=Decimal("0"))
    box_12_section_409a_deferrals: Decimal = Field(default=Decimal("0"))
    box_14_excess_golden_parachute: Decimal = Field(default=Decimal("0"))
    box_15_nonqualified_deferred_comp: Decimal = Field(default=Decimal("0"))
    state: Optional[str] = None
    state_id: Optional[str] = None
    state_tax_withheld: Decimal = Field(default=Decimal("0"))


# =============================================
# Aggregate Tax Input
# =============================================

class TradeHistoryEntry(BaseModel):
    """A purchase transaction from brokerage trade history (not on 1099-B).

    Used for cross-broker wash sale detection. Only purchases that were NOT
    sold in the tax year need to be included — sales are already on the 1099-B.
    """
    broker_name: str
    ticker: str = Field(description="Ticker symbol, e.g. VOO, MSFT")
    date_acquired: str = Field(description="Purchase date, e.g. 03/15/2025")
    shares: Decimal = Field(description="Number of shares purchased")


class Dependent(BaseModel):
    """A dependent claimed on the tax return."""
    name: str
    ssn: str
    relationship: str = Field(description="e.g. son, daughter, parent, other")
    age: int = Field(description="Age at end of tax year")


class TaxInput(BaseModel):
    """All extracted tax documents for one taxpayer (or couple if MFJ)."""
    tax_year: int = 2025
    filing_status: str = "single"

    first_name: str
    last_name: str
    ssn: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: str = "CA"
    zip_code: Optional[str] = None

    # Spouse fields (required for MFJ)
    spouse_first_name: Optional[str] = None
    spouse_last_name: Optional[str] = None
    spouse_ssn: Optional[str] = None

    # Dependents
    dependents: list[Dependent] = Field(default_factory=list)

    # Trade history (for cross-broker wash sale detection)
    trade_history: list[TradeHistoryEntry] = Field(default_factory=list)

    # Additional info (not from tax documents)
    charitable_contributions_cash: Decimal = Field(default=Decimal("0"))
    federal_estimated_payments: Decimal = Field(default=Decimal("0"))
    ca_estimated_payments: Decimal = Field(default=Decimal("0"))
    digital_assets: bool = Field(default=False)

    w2s: list[W2] = Field(default_factory=list)
    forms_1099_int: list[Form1099INT] = Field(default_factory=list)
    forms_1099_div: list[Form1099DIV] = Field(default_factory=list)
    forms_1099_nec: list[Form1099NEC] = Field(default_factory=list)
    forms_1099_b: list[Form1099B] = Field(default_factory=list)
    forms_1099_misc: list[Form1099MISC] = Field(default_factory=list)
    forms_1099_sa: list[Form1099SA] = Field(default_factory=list)
    forms_1098: list[Form1098] = Field(default_factory=list)
    forms_1098_e: list[Form1098E] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_mfj_fields(self) -> "TaxInput":
        if self.filing_status == "married_filing_jointly":
            if not self.spouse_first_name or not self.spouse_last_name or not self.spouse_ssn:
                raise ValueError(
                    "spouse_first_name, spouse_last_name, and spouse_ssn are required for MFJ"
                )
        return self


# =============================================
# Schedule Result Models
# =============================================

class Schedule1Result(BaseModel):
    """Schedule 1: Additional Income and Adjustments to Income."""
    # Part I - Additional Income
    line_3_business_income: Decimal = Decimal("0")
    line_5_rental_income: Decimal = Decimal("0")
    line_8a_other_income: Decimal = Decimal("0")
    line_10_total_additional_income: Decimal = Decimal("0")

    # Part II - Adjustments to Income
    line_15_se_tax_deduction: Decimal = Decimal("0")
    line_18_early_withdrawal_penalty: Decimal = Decimal("0")
    line_21_student_loan_interest: Decimal = Decimal("0")
    line_26_total_adjustments: Decimal = Decimal("0")


class Schedule2Result(BaseModel):
    """Schedule 2: Additional Taxes."""
    # Part I
    line_3_total: Decimal = Decimal("0")

    # Part II
    line_6_se_tax: Decimal = Decimal("0")
    line_11_additional_medicare: Decimal = Decimal("0")
    line_17_niit: Decimal = Decimal("0")
    line_21_total_additional_taxes: Decimal = Decimal("0")


class Schedule3Result(BaseModel):
    """Schedule 3: Additional Credits and Payments."""
    line_1_foreign_tax_credit: Decimal = Decimal("0")
    line_7_total: Decimal = Decimal("0")


class ScheduleAResult(BaseModel):
    """Schedule A: Itemized Deductions."""
    # Lines 5a-5e: State and local taxes (SALT)
    line_5a_state_local_income_tax: Decimal = Decimal("0")
    line_5b_state_local_property_tax: Decimal = Decimal("0")
    line_5d_salt_total: Decimal = Decimal("0")
    line_5e_salt_deduction: Decimal = Decimal("0")  # capped at $10,000

    # Lines 8-10: Interest you paid
    line_8a_mortgage_interest_1098: Decimal = Decimal("0")
    line_8c_points: Decimal = Decimal("0")
    line_10_total_interest: Decimal = Decimal("0")

    # Lines 11-14: Gifts to charity
    line_12_charitable_cash: Decimal = Decimal("0")

    # Line 17: Total itemized deductions
    line_17_total_itemized: Decimal = Decimal("0")

    # Whether itemized was chosen over standard deduction
    used_itemized: bool = False


class ScheduleBItem(BaseModel):
    payer_name: str
    amount: Decimal


class ScheduleBResult(BaseModel):
    """Schedule B: Interest and Ordinary Dividends."""
    interest_items: list[ScheduleBItem] = Field(default_factory=list)
    line_4_total_interest: Decimal = Decimal("0")

    dividend_items: list[ScheduleBItem] = Field(default_factory=list)
    line_6_total_dividends: Decimal = Decimal("0")

    has_foreign_accounts: bool = False
    has_foreign_trust: bool = False


class ScheduleDResult(BaseModel):
    """Schedule D: Capital Gains and Losses."""
    # Part I - Short-Term
    line_1a_short_term_basis_reported: Decimal = Decimal("0")
    line_1b_short_term_basis_not_reported: Decimal = Decimal("0")
    line_7_net_short_term: Decimal = Decimal("0")

    # Part II - Long-Term
    line_8a_long_term_basis_reported: Decimal = Decimal("0")
    line_8b_long_term_basis_not_reported: Decimal = Decimal("0")
    line_11_capital_gain_distributions: Decimal = Decimal("0")
    line_15_net_long_term: Decimal = Decimal("0")

    # Part III - Summary
    line_16_combine: Decimal = Decimal("0")
    line_21_net_capital_gain_loss: Decimal = Decimal("0")


class ScheduleSEResult(BaseModel):
    """Schedule SE: Self-Employment Tax."""
    line_2_net_se_earnings: Decimal = Decimal("0")
    line_3_92_35_pct: Decimal = Decimal("0")
    line_4a_ss_portion: Decimal = Decimal("0")
    line_4b_medicare_portion: Decimal = Decimal("0")
    line_12_se_tax: Decimal = Decimal("0")
    line_13_deductible_half: Decimal = Decimal("0")


class QDCGWorksheet(BaseModel):
    """Qualified Dividends and Capital Gain Tax Worksheet."""
    line_1_taxable_income: Decimal = Decimal("0")
    line_2_qualified_dividends: Decimal = Decimal("0")
    line_3_net_ltcg: Decimal = Decimal("0")
    line_4_sum: Decimal = Decimal("0")
    line_5_investment_income: Decimal = Decimal("0")
    line_6_ordinary_income: Decimal = Decimal("0")
    line_9_tax_on_ordinary: Decimal = Decimal("0")
    line_25_total_tax: Decimal = Decimal("0")


# =============================================
# Federal Tax Result
# =============================================

class FederalTaxResult(BaseModel):
    """Complete federal tax computation mapped to Form 1040 lines."""
    # Income (Lines 1-9)
    line_1a_wages: Decimal = Decimal("0")
    line_2a_tax_exempt_interest: Decimal = Decimal("0")
    line_2b_taxable_interest: Decimal = Decimal("0")
    line_3a_qualified_dividends: Decimal = Decimal("0")
    line_3b_ordinary_dividends: Decimal = Decimal("0")
    line_7_capital_gain_loss: Decimal = Decimal("0")
    line_8_other_income: Decimal = Decimal("0")
    line_9_total_income: Decimal = Decimal("0")

    # Adjustments (Lines 10-11)
    line_10_adjustments: Decimal = Decimal("0")
    line_11_adjusted_gross_income: Decimal = Decimal("0")

    # Deductions (Lines 12-15)
    line_12_standard_deduction: Decimal = Decimal("0")
    line_13_qualified_business_deduction: Decimal = Decimal("0")
    line_14_total_deductions: Decimal = Decimal("0")
    line_15_taxable_income: Decimal = Decimal("0")

    # Tax (Lines 16-24)
    line_16_tax: Decimal = Decimal("0")
    line_17_schedule_2_part1: Decimal = Decimal("0")
    line_18_sum: Decimal = Decimal("0")
    line_19_child_credit: Decimal = Decimal("0")
    line_20_schedule_3_part1: Decimal = Decimal("0")
    line_21_total_credits: Decimal = Decimal("0")
    line_22_after_credits: Decimal = Decimal("0")
    line_23_other_taxes: Decimal = Decimal("0")
    line_24_total_tax: Decimal = Decimal("0")

    # Payments (Lines 25-33)
    line_25a_w2_withheld: Decimal = Decimal("0")
    line_25b_1099_withheld: Decimal = Decimal("0")
    line_25d_total_withheld: Decimal = Decimal("0")
    line_33_total_payments: Decimal = Decimal("0")

    # Refund or Amount Owed (Lines 34-37)
    line_34_overpayment: Decimal = Decimal("0")
    line_35a_refund: Decimal = Decimal("0")
    line_37_amount_owed: Decimal = Decimal("0")

    # Schedule details
    schedule_a: Optional[ScheduleAResult] = None
    schedule_1: Optional[Schedule1Result] = None
    schedule_2: Optional[Schedule2Result] = None
    schedule_3: Optional[Schedule3Result] = None
    schedule_b: Optional[ScheduleBResult] = None
    schedule_d: Optional[ScheduleDResult] = None
    schedule_se: Optional[ScheduleSEResult] = None
    qdcg_worksheet: Optional[QDCGWorksheet] = None


# =============================================
# California Tax Result
# =============================================

class CaliforniaTaxResult(BaseModel):
    """California Form 540 computation."""
    federal_agi: Decimal = Decimal("0")
    ca_additions: Decimal = Decimal("0")
    ca_subtractions: Decimal = Decimal("0")
    ca_agi: Decimal = Decimal("0")

    ca_standard_deduction: Decimal = Decimal("0")
    ca_itemized_deduction: Decimal = Decimal("0")
    ca_used_itemized: bool = False
    ca_taxable_income: Decimal = Decimal("0")

    ca_tax: Decimal = Decimal("0")
    ca_exemption_credit: Decimal = Decimal("0")
    ca_tax_after_exemption: Decimal = Decimal("0")
    mental_health_surcharge: Decimal = Decimal("0")
    total_ca_tax: Decimal = Decimal("0")

    ca_tax_withheld: Decimal = Decimal("0")
    ca_estimated_payments: Decimal = Decimal("0")
    ca_sdi_withheld: Decimal = Decimal("0")
    total_payments: Decimal = Decimal("0")

    overpaid: Decimal = Decimal("0")
    amount_owed: Decimal = Decimal("0")
    refund: Decimal = Decimal("0")


# =============================================
# Complete Tax Return
# =============================================

class TaxReturn(BaseModel):
    """Complete tax return results."""
    input_data: TaxInput
    federal: FederalTaxResult
    california: CaliforniaTaxResult
