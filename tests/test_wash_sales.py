"""Tests for cross-broker wash sale detection."""

from decimal import Decimal

from src.calculators.wash_sales import (
    apply_cross_broker_wash_sales,
    extract_shares,
    extract_ticker,
    parse_date,
)
from src.models import (
    BasisReportedToIRS,
    Form1099B,
    Form1099BTransaction,
    TaxInput,
    TermType,
)


class TestExtractTicker:
    def test_standard_format(self):
        assert extract_ticker("236 sh VANGUARD S&P 500 ETF (VOO)") == "VOO"

    def test_nvidia(self):
        assert extract_ticker("42.142 sh NVIDIA CORP (NVDA)") == "NVDA"

    def test_with_suffix(self):
        assert extract_ticker("0.064 Bitcoin (BTC) - Digital Asset") == "BTC"

    def test_no_ticker(self):
        assert extract_ticker("MICROSOFT CORP") is None

    def test_no_parens(self):
        assert extract_ticker("some random text") is None

    def test_microsoft(self):
        assert extract_ticker("0.506 sh MICROSOFT CORP (MSFT)") == "MSFT"


class TestExtractShares:
    def test_integer(self):
        assert extract_shares("236 sh VANGUARD S&P 500 ETF (VOO)") == Decimal("236")

    def test_decimal(self):
        assert extract_shares("42.142 sh NVIDIA CORP (NVDA)") == Decimal("42.142")

    def test_no_shares(self):
        assert extract_shares("MICROSOFT CORP") is None


class TestParseDate:
    def test_standard(self):
        from datetime import date
        assert parse_date("01/24/2023") == date(2023, 1, 24)

    def test_various(self):
        assert parse_date("Various") is None

    def test_none(self):
        assert parse_date(None) is None


def _make_cross_broker_input(
    broker1_sale_loss: Decimal = Decimal("-1000"),
    broker1_sale_date: str = "04/07/2025",
    broker1_acq_date: str = "01/15/2025",
    broker2_acq_date: str = "04/01/2025",
    broker2_shares: str = "100",
    broker1_shares: str = "100",
    broker1_wash: Decimal = Decimal("0"),
    same_ticker: bool = True,
) -> TaxInput:
    """Create a TaxInput with two brokers for wash sale testing."""
    proceeds = Decimal("5000")
    cost = proceeds - broker1_sale_loss  # loss is negative, so cost > proceeds

    ticker2 = "VOO" if same_ticker else "AAPL"

    return TaxInput(
        first_name="Test", last_name="User", ssn="111-22-3333", state="CA",
        forms_1099_b=[
            Form1099B(
                broker_name="Broker A",
                recipient_name="Test User",
                recipient_tin="111-22-3333",
                transactions=[
                    Form1099BTransaction(
                        description=f"{broker1_shares} sh VANGUARD S&P 500 ETF (VOO)",
                        date_acquired=broker1_acq_date,
                        date_sold=broker1_sale_date,
                        proceeds=proceeds,
                        cost_basis=cost,
                        wash_sale_loss_disallowed=broker1_wash,
                        term=TermType.SHORT_TERM,
                        basis_reported_to_irs=BasisReportedToIRS.YES,
                    )
                ],
            ),
            Form1099B(
                broker_name="Broker B",
                recipient_name="Test User",
                recipient_tin="111-22-3333",
                transactions=[
                    Form1099BTransaction(
                        description=f"{broker2_shares} sh VANGUARD S&P 500 ETF ({ticker2})",
                        date_acquired=broker2_acq_date,
                        date_sold="12/31/2025",
                        proceeds=Decimal("6000"),
                        cost_basis=Decimal("5800"),
                        term=TermType.SHORT_TERM,
                        basis_reported_to_irs=BasisReportedToIRS.YES,
                    )
                ],
            ),
        ],
    )


class TestCrossBrokerWashSale:
    def test_loss_disallowed_when_cross_broker_purchase_within_30_days(self):
        """Sale at loss at Broker A, purchase within 30 days at Broker B → wash sale."""
        ti = _make_cross_broker_input(
            broker1_sale_loss=Decimal("-1000"),
            broker1_sale_date="04/07/2025",
            broker2_acq_date="04/01/2025",  # 6 days before sale — within 30 days
        )
        txn = ti.forms_1099_b[0].transactions[0]
        assert txn.wash_sale_loss_disallowed == Decimal("0")  # before

        apply_cross_broker_wash_sales(ti)

        assert txn.wash_sale_loss_disallowed > Decimal("0")  # loss disallowed
        # gain_or_loss should be recomputed: proceeds - cost + wash_disallowed = closer to 0
        assert txn.gain_or_loss > Decimal("-1000")

    def test_no_wash_sale_outside_30_day_window(self):
        """Purchase more than 30 days away → no wash sale."""
        ti = _make_cross_broker_input(
            broker1_sale_loss=Decimal("-1000"),
            broker1_sale_date="04/07/2025",
            broker2_acq_date="01/01/2025",  # 96 days before sale — outside window
        )
        txn = ti.forms_1099_b[0].transactions[0]
        apply_cross_broker_wash_sales(ti)
        assert txn.wash_sale_loss_disallowed == Decimal("0")

    def test_no_wash_sale_for_different_ticker(self):
        """Different security at other broker → no wash sale."""
        ti = _make_cross_broker_input(
            broker1_sale_loss=Decimal("-1000"),
            same_ticker=False,
        )
        txn = ti.forms_1099_b[0].transactions[0]
        apply_cross_broker_wash_sales(ti)
        assert txn.wash_sale_loss_disallowed == Decimal("0")

    def test_no_wash_sale_for_gain(self):
        """Sale at a gain → no wash sale regardless of timing."""
        ti = _make_cross_broker_input(
            broker1_sale_loss=Decimal("500"),  # positive = gain
            broker2_acq_date="04/01/2025",
        )
        txn = ti.forms_1099_b[0].transactions[0]
        apply_cross_broker_wash_sales(ti)
        assert txn.wash_sale_loss_disallowed == Decimal("0")

    def test_partial_wash_sale(self):
        """Sell 100 shares at loss, buy only 50 at other broker → partial disallowance."""
        ti = _make_cross_broker_input(
            broker1_sale_loss=Decimal("-1000"),
            broker1_shares="100",
            broker2_shares="50",
            broker2_acq_date="04/01/2025",
        )
        txn = ti.forms_1099_b[0].transactions[0]
        apply_cross_broker_wash_sales(ti)
        # Should disallow ~50% of the $1000 loss = ~$500
        assert Decimal("400") < txn.wash_sale_loss_disallowed < Decimal("600")

    def test_single_broker_no_effect(self):
        """With only one broker, no cross-broker wash sales possible."""
        ti = TaxInput(
            first_name="Test", last_name="User", ssn="111-22-3333", state="CA",
            forms_1099_b=[
                Form1099B(
                    broker_name="Only Broker",
                    recipient_name="Test User",
                    recipient_tin="111-22-3333",
                    transactions=[
                        Form1099BTransaction(
                            description="100 sh VOO (VOO)",
                            date_acquired="01/15/2025",
                            date_sold="04/07/2025",
                            proceeds=Decimal("5000"),
                            cost_basis=Decimal("6000"),
                            term=TermType.SHORT_TERM,
                            basis_reported_to_irs=BasisReportedToIRS.YES,
                        )
                    ],
                ),
            ],
        )
        txn = ti.forms_1099_b[0].transactions[0]
        apply_cross_broker_wash_sales(ti)
        assert txn.wash_sale_loss_disallowed == Decimal("0")

    def test_broker_already_disallowed_not_doubled(self):
        """If broker already disallowed the full loss, don't add more."""
        ti = _make_cross_broker_input(
            broker1_sale_loss=Decimal("-1000"),
            broker1_wash=Decimal("1000"),  # broker already disallowed full amount
            broker2_acq_date="04/01/2025",
        )
        txn = ti.forms_1099_b[0].transactions[0]
        apply_cross_broker_wash_sales(ti)
        assert txn.wash_sale_loss_disallowed == Decimal("1000")  # unchanged

    def test_various_date_skipped(self):
        """Transactions with 'Various' dates are skipped."""
        ti = _make_cross_broker_input(
            broker1_sale_loss=Decimal("-1000"),
            broker1_sale_date="Various",
            broker2_acq_date="04/01/2025",
        )
        txn = ti.forms_1099_b[0].transactions[0]
        apply_cross_broker_wash_sales(ti)
        assert txn.wash_sale_loss_disallowed == Decimal("0")
