---
name: tax-filing
description: Process W2, 1099, and 1098 PDFs to prepare 2025 federal and California tax returns
---

# Tax Filing Skill

Process W2 and 1099 PDF documents to calculate and generate 2025 Federal Form 1040 and California Form 540 tax returns.

## Workflow

### Step 1: Identify Input Documents

Ask the user for the paths to their W2, 1099, and 1098 PDF files, or look in the `input/` directory. Identify each document type:
- W-2, 1099-INT, 1099-DIV, 1099-NEC, 1099-B, 1099-MISC, 1099-SA, 1098, 1098-E

### Step 2: Extract Data from Each PDF

Use the Read tool to view each PDF and extract structured data.

**For W-2**, extract:
```json
{
  "employer_ein": "XX-XXXXXXX",
  "employer_name": "...",
  "employee_ssn": "XXX-XX-XXXX",
  "employee_name": "...",
  "wages_tips_other_comp": "0.00",
  "federal_income_tax_withheld": "0.00",
  "social_security_wages": "0.00",
  "social_security_tax_withheld": "0.00",
  "medicare_wages_and_tips": "0.00",
  "medicare_tax_withheld": "0.00",
  "social_security_tips": "0.00",
  "allocated_tips": "0.00",
  "dependent_care_benefits": "0.00",
  "nonqualified_plans": "0.00",
  "box_12_codes": [{"code": "D", "amount": "0.00"}],
  "statutory_employee": false,
  "retirement_plan": true,
  "third_party_sick_pay": false,
  "box_14_other": [{"description": "CA SDI/VPDI", "amount": "0.00"}],
  "state": "CA",
  "state_employer_id": "...",
  "state_wages": "0.00",
  "state_income_tax": "0.00",
  "local_wages": "0.00",
  "local_income_tax": "0.00",
  "locality_name": null
}
```

**For 1099-INT**, extract:
```json
{
  "payer_name": "...",
  "recipient_name": "...",
  "recipient_tin": "XXX-XX-XXXX",
  "box_1_interest_income": "0.00",
  "box_2_early_withdrawal_penalty": "0.00",
  "box_3_us_savings_bond_interest": "0.00",
  "box_4_federal_tax_withheld": "0.00",
  "box_6_foreign_tax_paid": "0.00",
  "box_8_tax_exempt_interest": "0.00",
  "state": "CA",
  "state_tax_withheld": "0.00"
}
```

**For 1099-DIV**, extract:
```json
{
  "payer_name": "...",
  "recipient_name": "...",
  "recipient_tin": "XXX-XX-XXXX",
  "box_1a_ordinary_dividends": "0.00",
  "box_1b_qualified_dividends": "0.00",
  "box_2a_total_capital_gain": "0.00",
  "box_4_federal_tax_withheld": "0.00",
  "box_7_foreign_tax_paid": "0.00",
  "state": "CA",
  "state_tax_withheld": "0.00"
}
```

**For 1099-NEC**, extract:
```json
{
  "payer_name": "...",
  "recipient_name": "...",
  "recipient_tin": "XXX-XX-XXXX",
  "box_1_nonemployee_compensation": "0.00",
  "box_4_federal_tax_withheld": "0.00",
  "state": "CA",
  "state_income_tax_withheld": "0.00"
}
```

**For 1099-B**, extract each transaction:
```json
{
  "broker_name": "...",
  "recipient_name": "...",
  "recipient_tin": "XXX-XX-XXXX",
  "transactions": [
    {
      "description": "100 sh AAPL",
      "date_acquired": "01/15/2024",
      "date_sold": "03/20/2025",
      "proceeds": "15000.00",
      "cost_basis": "12000.00",
      "wash_sale_loss_disallowed": "0.00",
      "term": "long_term",
      "basis_reported_to_irs": "yes",
      "federal_tax_withheld": "0.00"
    }
  ]
}
```

**For 1099-MISC**, extract:
```json
{
  "payer_name": "...",
  "recipient_name": "...",
  "recipient_tin": "XXX-XX-XXXX",
  "box_1_rents": "0.00",
  "box_3_other_income": "0.00",
  "box_4_federal_tax_withheld": "0.00",
  "state": "CA",
  "state_tax_withheld": "0.00"
}
```

**For 1099-SA** (HSA/MSA Distributions), extract:
```json
{
  "payer_name": "...",
  "recipient_name": "...",
  "recipient_tin": "XXX-XX-XXXX",
  "box_1_gross_distribution": "0.00",
  "box_2_earnings_on_excess": "0.00",
  "box_3_distribution_code": "1",
  "box_5_account_type": "HSA",
  "qualified": true
}
```

**For 1098** (Mortgage Interest Statement), extract:
```json
{
  "lender_name": "...",
  "borrower_name": "...",
  "borrower_ssn": "XXX-XX-XXXX",
  "box_1_mortgage_interest": "0.00",
  "box_2_outstanding_principal": "0.00",
  "box_5_mortgage_insurance_premiums": "0.00",
  "box_6_points_paid": "0.00",
  "box_10_property_tax": "0.00"
}
```

**For 1098-E** (Student Loan Interest Statement), extract:
```json
{
  "lender_name": "...",
  "borrower_name": "...",
  "borrower_ssn": "XXX-XX-XXXX",
  "box_1_student_loan_interest_paid": "0.00",
  "box_2_capitalized_interest": false
}
```

### Step 2.5: Ask Additional Questions

After extracting all PDF data and confirming filing status, ask the user these questions:

1. **Dependents**: "Do you have any dependents (children or others you support)? If yes, provide each dependent's name, SSN, relationship (e.g. son, daughter), and age at end of 2025."
2. **Charitable contributions**: "Did you make any charitable cash donations in 2025? If yes, what was the total amount?"
3. **Estimated tax payments**: "Did you make any estimated tax payments (quarterly) for 2025? If yes, how much total for federal and how much for California?"
4. **Digital assets**: Auto-detect from 1099-B/1099-DA — if any crypto or digital asset transactions exist, set `digital_assets` to `true`. Otherwise ask: "Did you sell, exchange, or otherwise dispose of any digital assets (cryptocurrency, NFTs) in 2025?"
5. **Brokerage trade history** (for cross-broker wash sales): If any 1099-B transactions show sales at a loss, ask: "Do you have brokerage trade history or account statements from other brokers showing purchases of the same securities (e.g. VOO, MSFT) within 30 days of those loss sales? If so, provide the PDF or CSV files so we can check for cross-broker wash sales." Extract purchase entries from those files into `trade_history`.

Add the answers to the JSON in Step 3.

### Step 3: Assemble Tax Input JSON

Combine all extracted documents into a single JSON file. Get personal info from the W-2 employee fields.

For **Single** filing:
```json
{
  "tax_year": 2025,
  "filing_status": "single",
  "first_name": "...",
  "last_name": "...",
  "ssn": "XXX-XX-XXXX",
  "state": "CA",
  "trade_history": [],
  "dependents": [],
  "charitable_contributions_cash": "0.00",
  "federal_estimated_payments": "0.00",
  "ca_estimated_payments": "0.00",
  "digital_assets": false,
  "w2s": [...],
  "forms_1099_int": [...],
  "forms_1099_div": [...],
  "forms_1099_nec": [...],
  "forms_1099_b": [...],
  "forms_1099_misc": [],
  "forms_1099_sa": [],
  "forms_1098": [],
  "forms_1098_e": []
}
```

For **Married Filing Jointly (MFJ)**: include spouse info, and put W2s/1099s from BOTH spouses into the same lists:
```json
{
  "tax_year": 2025,
  "filing_status": "married_filing_jointly",
  "first_name": "...",
  "last_name": "...",
  "ssn": "XXX-XX-XXXX",
  "spouse_first_name": "...",
  "spouse_last_name": "...",
  "spouse_ssn": "XXX-XX-XXXX",
  "state": "CA",
  "trade_history": [{"broker_name": "Fidelity", "ticker": "VOO", "date_acquired": "03/20/2025", "shares": "50"}],
  "dependents": [{"name": "...", "ssn": "XXX-XX-XXXX", "relationship": "son", "age": 5}],
  "charitable_contributions_cash": "0.00",
  "federal_estimated_payments": "0.00",
  "ca_estimated_payments": "0.00",
  "digital_assets": false,
  "w2s": ["... both spouses' W-2s ..."],
  "forms_1099_int": ["... both spouses' 1099-INTs ..."],
  "forms_1099_div": ["... both spouses' 1099-DIVs ..."],
  "forms_1099_nec": [],
  "forms_1099_b": ["... both spouses' 1099-Bs ..."],
  "forms_1099_misc": [],
  "forms_1099_sa": ["... any 1099-SA HSA distribution forms ..."],
  "forms_1098": ["... any 1098 mortgage interest forms ..."],
  "forms_1098_e": ["... any 1098-E forms ..."]
}
```

Save this to `input/tax_data.json`.

### Step 4: Run Tax Calculations

```bash
python main.py --input input/tax_data.json --output output/
```

### Step 5: Review and Present Results

Read `output/2025_tax_return.txt` and present the key results:
- Federal AGI, total tax, refund or amount owed
- California AGI, total tax, refund or amount owed
- Combined total

### Extraction Rules

- All monetary amounts as strings with two decimal places (e.g., "12345.67")
- Empty or zero boxes: use "0.00"
- For 1099-B `term`: use "short_term" (held <= 1 year), "long_term" (held > 1 year), or "unknown"
- For 1099-B `basis_reported_to_irs`: use "yes", "no", or "unknown"
- The employee SSN from the first W-2 becomes the taxpayer SSN
- For W-2 Box 14 items, preserve the exact label text (needed to identify CA SDI)
- Include all Box 12 codes with their letter code and amount
- For MFJ: put ALL W-2s and 1099s from both spouses into the same lists — the calculators aggregate across all documents automatically
- For MFJ: `spouse_first_name`, `spouse_last_name`, and `spouse_ssn` are required
- For 1099-SA: set `qualified` to `true` if the distribution was used for qualified medical expenses (the common case). Ask the user if unsure. Set to `false` only if the user confirms the distribution was NOT for medical expenses — this triggers taxable income + 20% penalty.
- For 1099-SA `box_3_distribution_code`: use "1" (Normal), "2" (Excess contributions), "3" (Disability), "4" (Death), "5" (Prohibited transaction), or "6" (Transfer)
- For 1099-SA `box_5_account_type`: use "HSA", "Archer MSA", or "MA MSA"
- For trade history entries: only include **purchases** of securities that were NOT sold in 2025 (sales are already on 1099-B). Each entry needs `broker_name`, `ticker` (symbol), `date_acquired` (purchase date), and `shares` (quantity). Extract these from brokerage trade confirmations, account statements, or CSV exports.
- 1098 `box_10_property_tax` may be blank on many 1098 forms — use "0.00" if not present
- 1098 `borrower_name` should match the name on the form (may be either spouse)
- 1098-E `borrower_name` should match the name on the form (may be either spouse)
