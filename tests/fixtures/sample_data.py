"""Sample tax data for testing."""

from decimal import Decimal

from src.models import (
    BasisReportedToIRS,
    Form1098,
    Form1099B,
    Form1099BTransaction,
    Form1099DIV,
    Form1099INT,
    Form1099MISC,
    Form1099NEC,
    TaxInput,
    TermType,
    W2,
    W2Box12,
    W2Box14,
)


def make_simple_w2_only() -> TaxInput:
    """Single W2, $100k salary, no other income."""
    return TaxInput(
        first_name="John",
        last_name="Doe",
        ssn="123-45-6789",
        state="CA",
        w2s=[
            W2(
                employer_ein="12-3456789",
                employer_name="Acme Corp",
                employee_ssn="123-45-6789",
                employee_name="John Doe",
                wages_tips_other_comp=Decimal("100000"),
                federal_income_tax_withheld=Decimal("15000"),
                social_security_wages=Decimal("100000"),
                social_security_tax_withheld=Decimal("6200"),
                medicare_wages_and_tips=Decimal("100000"),
                medicare_tax_withheld=Decimal("1450"),
                retirement_plan=True,
                box_12_codes=[W2Box12(code="D", amount=Decimal("20000"))],
                box_14_other=[
                    W2Box14(description="CA SDI/VPDI", amount=Decimal("1200"))
                ],
                state="CA",
                state_employer_id="123-4567-8",
                state_wages=Decimal("100000"),
                state_income_tax=Decimal("5500"),
            )
        ],
    )


def make_w2_plus_investments() -> TaxInput:
    """W2 at $150k + interest + dividends + capital gains."""
    return TaxInput(
        first_name="Jane",
        last_name="Smith",
        ssn="987-65-4321",
        state="CA",
        w2s=[
            W2(
                employer_ein="98-7654321",
                employer_name="Tech Inc",
                employee_ssn="987-65-4321",
                employee_name="Jane Smith",
                wages_tips_other_comp=Decimal("150000"),
                federal_income_tax_withheld=Decimal("28000"),
                social_security_wages=Decimal("150000"),
                social_security_tax_withheld=Decimal("9300"),
                medicare_wages_and_tips=Decimal("150000"),
                medicare_tax_withheld=Decimal("2175"),
                retirement_plan=True,
                box_14_other=[
                    W2Box14(description="CASDI", amount=Decimal("1800"))
                ],
                state="CA",
                state_wages=Decimal("150000"),
                state_income_tax=Decimal("9000"),
            )
        ],
        forms_1099_int=[
            Form1099INT(
                payer_name="Big Bank",
                recipient_name="Jane Smith",
                recipient_tin="987-65-4321",
                box_1_interest_income=Decimal("2000"),
                box_6_foreign_tax_paid=Decimal("50"),
                state="CA",
            )
        ],
        forms_1099_div=[
            Form1099DIV(
                payer_name="Vanguard",
                recipient_name="Jane Smith",
                recipient_tin="987-65-4321",
                box_1a_ordinary_dividends=Decimal("5000"),
                box_1b_qualified_dividends=Decimal("3500"),
                box_2a_total_capital_gain=Decimal("1000"),
                box_7_foreign_tax_paid=Decimal("100"),
                state="CA",
            )
        ],
        forms_1099_b=[
            Form1099B(
                broker_name="Fidelity",
                recipient_name="Jane Smith",
                recipient_tin="987-65-4321",
                transactions=[
                    Form1099BTransaction(
                        description="100 sh AAPL",
                        date_acquired="01/15/2024",
                        date_sold="06/20/2025",
                        proceeds=Decimal("20000"),
                        cost_basis=Decimal("15000"),
                        term=TermType.LONG_TERM,
                        basis_reported_to_irs=BasisReportedToIRS.YES,
                    ),
                    Form1099BTransaction(
                        description="50 sh MSFT",
                        date_acquired="09/01/2025",
                        date_sold="11/15/2025",
                        proceeds=Decimal("8000"),
                        cost_basis=Decimal("7500"),
                        term=TermType.SHORT_TERM,
                        basis_reported_to_irs=BasisReportedToIRS.YES,
                    ),
                ],
            )
        ],
    )


def make_self_employed() -> TaxInput:
    """1099-NEC at $80k, no W2 - triggers Schedule SE."""
    return TaxInput(
        first_name="Bob",
        last_name="Freelance",
        ssn="555-12-3456",
        state="CA",
        forms_1099_nec=[
            Form1099NEC(
                payer_name="Client Corp",
                recipient_name="Bob Freelance",
                recipient_tin="555-12-3456",
                box_1_nonemployee_compensation=Decimal("80000"),
                state="CA",
                state_income_tax_withheld=Decimal("0"),
            )
        ],
    )


def make_high_income() -> TaxInput:
    """$400k W2 + investments - triggers additional Medicare and NIIT."""
    return TaxInput(
        first_name="Alice",
        last_name="Executive",
        ssn="111-22-3333",
        state="CA",
        w2s=[
            W2(
                employer_ein="11-2233344",
                employer_name="BigCo",
                employee_ssn="111-22-3333",
                employee_name="Alice Executive",
                wages_tips_other_comp=Decimal("400000"),
                federal_income_tax_withheld=Decimal("100000"),
                social_security_wages=Decimal("176100"),
                social_security_tax_withheld=Decimal("10918.20"),
                medicare_wages_and_tips=Decimal("400000"),
                medicare_tax_withheld=Decimal("5800"),
                retirement_plan=True,
                box_14_other=[
                    W2Box14(description="CA SDI", amount=Decimal("1800"))
                ],
                state="CA",
                state_wages=Decimal("400000"),
                state_income_tax=Decimal("30000"),
            )
        ],
        forms_1099_int=[
            Form1099INT(
                payer_name="Treasury Direct",
                recipient_name="Alice Executive",
                recipient_tin="111-22-3333",
                box_1_interest_income=Decimal("10000"),
                box_3_us_savings_bond_interest=Decimal("5000"),
                state="CA",
            )
        ],
        forms_1099_div=[
            Form1099DIV(
                payer_name="Schwab",
                recipient_name="Alice Executive",
                recipient_tin="111-22-3333",
                box_1a_ordinary_dividends=Decimal("20000"),
                box_1b_qualified_dividends=Decimal("15000"),
                box_2a_total_capital_gain=Decimal("5000"),
                state="CA",
            )
        ],
    )


def make_with_mortgage() -> TaxInput:
    """$200k salary + mortgage interest - triggers Schedule A itemized deductions."""
    return TaxInput(
        first_name="Mike",
        last_name="Homeowner",
        ssn="222-33-4444",
        state="CA",
        w2s=[
            W2(
                employer_ein="22-3344455",
                employer_name="Employer Inc",
                employee_ssn="222-33-4444",
                employee_name="Mike Homeowner",
                wages_tips_other_comp=Decimal("200000"),
                federal_income_tax_withheld=Decimal("40000"),
                social_security_wages=Decimal("176100"),
                social_security_tax_withheld=Decimal("10918.20"),
                medicare_wages_and_tips=Decimal("200000"),
                medicare_tax_withheld=Decimal("2900"),
                retirement_plan=True,
                box_14_other=[
                    W2Box14(description="CA SDI", amount=Decimal("2400"))
                ],
                state="CA",
                state_employer_id="222-3344-5",
                state_wages=Decimal("200000"),
                state_income_tax=Decimal("14000"),
            )
        ],
        forms_1098=[
            Form1098(
                lender_name="Wells Fargo Home Mortgage",
                borrower_name="Mike Homeowner",
                borrower_ssn="222-33-4444",
                box_1_mortgage_interest=Decimal("18000"),
                box_2_outstanding_principal=Decimal("450000"),
                box_6_points_paid=Decimal("0"),
                box_10_property_tax=Decimal("8000"),
            )
        ],
    )


def make_with_small_mortgage() -> TaxInput:
    """$100k salary + small mortgage - itemized < standard, should use standard."""
    return TaxInput(
        first_name="Sam",
        last_name="Renter",
        ssn="333-44-5555",
        state="CA",
        w2s=[
            W2(
                employer_ein="33-4455566",
                employer_name="Small Co",
                employee_ssn="333-44-5555",
                employee_name="Sam Renter",
                wages_tips_other_comp=Decimal("100000"),
                federal_income_tax_withheld=Decimal("15000"),
                social_security_wages=Decimal("100000"),
                social_security_tax_withheld=Decimal("6200"),
                medicare_wages_and_tips=Decimal("100000"),
                medicare_tax_withheld=Decimal("1450"),
                box_14_other=[
                    W2Box14(description="CA SDI", amount=Decimal("1200"))
                ],
                state="CA",
                state_wages=Decimal("100000"),
                state_income_tax=Decimal("5500"),
            )
        ],
        forms_1098=[
            Form1098(
                lender_name="Local Credit Union",
                borrower_name="Sam Renter",
                borrower_ssn="333-44-5555",
                box_1_mortgage_interest=Decimal("3000"),
                box_2_outstanding_principal=Decimal("100000"),
            )
        ],
    )


def make_capital_loss() -> TaxInput:
    """Scenario with capital losses exceeding $3k limit."""
    return TaxInput(
        first_name="Charlie",
        last_name="Loser",
        ssn="444-55-6666",
        state="CA",
        w2s=[
            W2(
                employer_ein="44-5566677",
                employer_name="Stable Inc",
                employee_ssn="444-55-6666",
                employee_name="Charlie Loser",
                wages_tips_other_comp=Decimal("75000"),
                federal_income_tax_withheld=Decimal("10000"),
                social_security_wages=Decimal("75000"),
                social_security_tax_withheld=Decimal("4650"),
                medicare_wages_and_tips=Decimal("75000"),
                medicare_tax_withheld=Decimal("1087.50"),
                state="CA",
                state_wages=Decimal("75000"),
                state_income_tax=Decimal("3500"),
                box_14_other=[
                    W2Box14(description="CA SDI", amount=Decimal("900"))
                ],
            )
        ],
        forms_1099_b=[
            Form1099B(
                broker_name="Robinhood",
                recipient_name="Charlie Loser",
                recipient_tin="444-55-6666",
                transactions=[
                    Form1099BTransaction(
                        description="SPAC Holdings",
                        date_acquired="03/01/2024",
                        date_sold="08/15/2025",
                        proceeds=Decimal("2000"),
                        cost_basis=Decimal("15000"),
                        term=TermType.LONG_TERM,
                        basis_reported_to_irs=BasisReportedToIRS.YES,
                    ),
                ],
            )
        ],
    )
