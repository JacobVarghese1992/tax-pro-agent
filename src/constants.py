"""Tax year 2025 brackets, rates, thresholds, and limits for federal and California."""

from decimal import Decimal

TAX_YEAR = 2025

# =============================================
# FEDERAL TAX CONSTANTS (Single filer)
# =============================================

# (upper_limit, marginal_rate) - last bracket uses a very large upper limit
FEDERAL_BRACKETS_SINGLE = [
    (Decimal("11925"), Decimal("0.10")),
    (Decimal("48475"), Decimal("0.12")),
    (Decimal("103350"), Decimal("0.22")),
    (Decimal("197300"), Decimal("0.24")),
    (Decimal("250525"), Decimal("0.32")),
    (Decimal("626350"), Decimal("0.35")),
    (Decimal("999999999"), Decimal("0.37")),
]

FEDERAL_STANDARD_DEDUCTION_SINGLE = Decimal("15000")

# Capital gains / qualified dividends brackets (Single, 2025)
LTCG_0_THRESHOLD = Decimal("48475")
LTCG_15_THRESHOLD = Decimal("533400")
# 20% applies above LTCG_15_THRESHOLD

# Social Security
SS_WAGE_BASE = Decimal("176100")
SS_RATE_EMPLOYEE = Decimal("0.062")
SS_RATE_SELF_EMPLOYED = Decimal("0.124")
MEDICARE_RATE_EMPLOYEE = Decimal("0.0145")
MEDICARE_RATE_SELF_EMPLOYED = Decimal("0.029")
ADDITIONAL_MEDICARE_THRESHOLD_SINGLE = Decimal("200000")
ADDITIONAL_MEDICARE_RATE = Decimal("0.009")

# Self-employment
SE_INCOME_FACTOR = Decimal("0.9235")

# Net Investment Income Tax (NIIT)
NIIT_THRESHOLD_SINGLE = Decimal("200000")
NIIT_RATE = Decimal("0.038")

# Capital loss deduction limit
CAPITAL_LOSS_LIMIT = Decimal("3000")

# Schedule B filing threshold
SCHEDULE_B_THRESHOLD = Decimal("1500")

# Foreign tax credit simplified limit (can take direct credit without Form 1116)
FOREIGN_TAX_CREDIT_SIMPLIFIED_LIMIT = Decimal("300")

# =============================================
# CALIFORNIA TAX CONSTANTS (Single filer)
# =============================================

CA_BRACKETS_SINGLE = [
    (Decimal("10756"), Decimal("0.01")),
    (Decimal("25499"), Decimal("0.02")),
    (Decimal("40245"), Decimal("0.04")),
    (Decimal("55866"), Decimal("0.06")),
    (Decimal("70606"), Decimal("0.08")),
    (Decimal("360659"), Decimal("0.093")),
    (Decimal("432787"), Decimal("0.103")),
    (Decimal("721314"), Decimal("0.113")),
    (Decimal("1000000"), Decimal("0.123")),
    (Decimal("999999999"), Decimal("0.133")),
]

CA_STANDARD_DEDUCTION_SINGLE = Decimal("5540")
CA_PERSONAL_EXEMPTION_CREDIT = Decimal("149")
CA_MENTAL_HEALTH_THRESHOLD = Decimal("1000000")
CA_MENTAL_HEALTH_RATE = Decimal("0.01")

# =============================================
# FEDERAL TAX CONSTANTS (Married Filing Jointly)
# =============================================

FEDERAL_BRACKETS_MFJ = [
    (Decimal("23850"), Decimal("0.10")),
    (Decimal("96950"), Decimal("0.12")),
    (Decimal("206700"), Decimal("0.22")),
    (Decimal("395450"), Decimal("0.24")),
    (Decimal("501050"), Decimal("0.32")),
    (Decimal("751600"), Decimal("0.35")),
    (Decimal("999999999"), Decimal("0.37")),
]

FEDERAL_STANDARD_DEDUCTION_MFJ = Decimal("30000")

LTCG_0_THRESHOLD_MFJ = Decimal("96700")
LTCG_15_THRESHOLD_MFJ = Decimal("600050")

ADDITIONAL_MEDICARE_THRESHOLD_MFJ = Decimal("250000")
NIIT_THRESHOLD_MFJ = Decimal("250000")

FOREIGN_TAX_CREDIT_SIMPLIFIED_LIMIT_MFJ = Decimal("600")

# =============================================
# HSA (Form 1099-SA / Form 8889)
# =============================================

HSA_NONQUALIFIED_PENALTY_RATE = Decimal("0.20")

# =============================================
# SCHEDULE A: ITEMIZED DEDUCTIONS
# =============================================

# Federal SALT deduction cap ($10,000 for both single and MFJ, per TCJA through 2025)
SALT_DEDUCTION_LIMIT = Decimal("10000")

# =============================================
# STUDENT LOAN INTEREST DEDUCTION (1098-E)
# =============================================

STUDENT_LOAN_INTEREST_MAX_DEDUCTION = Decimal("2500")

STUDENT_LOAN_PHASEOUT_START_SINGLE = Decimal("85000")
STUDENT_LOAN_PHASEOUT_END_SINGLE = Decimal("100000")

STUDENT_LOAN_PHASEOUT_START_MFJ = Decimal("170000")
STUDENT_LOAN_PHASEOUT_END_MFJ = Decimal("200000")

# =============================================
# CALIFORNIA TAX CONSTANTS (Married Filing Jointly)
# =============================================

CA_BRACKETS_MFJ = [
    (Decimal("21512"), Decimal("0.01")),
    (Decimal("50998"), Decimal("0.02")),
    (Decimal("80490"), Decimal("0.04")),
    (Decimal("111732"), Decimal("0.06")),
    (Decimal("141212"), Decimal("0.08")),
    (Decimal("721318"), Decimal("0.093")),
    (Decimal("865574"), Decimal("0.103")),
    (Decimal("1442628"), Decimal("0.113")),
    (Decimal("2000000"), Decimal("0.123")),
    (Decimal("999999999"), Decimal("0.133")),
]

CA_STANDARD_DEDUCTION_MFJ = Decimal("11080")
CA_PERSONAL_EXEMPTION_CREDIT_MFJ = Decimal("298")
CA_MENTAL_HEALTH_THRESHOLD_MFJ = Decimal("2000000")
