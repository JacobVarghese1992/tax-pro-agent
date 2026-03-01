"""Cross-broker wash sale detection and adjustment.

Brokers only report wash sales within their own accounts. This module
detects wash sales across different brokers by matching securities sold
at a loss with purchases of the same security within ±30 days at other
brokers, per IRS Section 1091.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from src.models import TaxInput

WASH_SALE_WINDOW = timedelta(days=30)


def extract_ticker(description: str) -> str | None:
    """Extract ticker symbol from a transaction description.

    Looks for a parenthesized ticker at the end of the description, e.g.:
        "236 sh VANGUARD S&P 500 ETF (VOO)" -> "VOO"
        "42.142 sh NVIDIA CORP (NVDA)" -> "NVDA"
        "0.064 Bitcoin (BTC) - Digital Asset" -> "BTC"
        "MICROSOFT CORP" -> None (no ticker in parens)
    """
    match = re.search(r"\(([A-Z]{1,5})\)", description)
    return match.group(1) if match else None


def extract_shares(description: str) -> Decimal | None:
    """Extract the number of shares from a transaction description.

    E.g. "236 sh VANGUARD S&P 500 ETF (VOO)" -> Decimal("236")
         "42.142 sh NVIDIA CORP (NVDA)" -> Decimal("42.142")
    """
    match = re.match(r"([\d.]+)\s+sh\b", description)
    if match:
        try:
            return Decimal(match.group(1))
        except Exception:
            return None
    return None


def parse_date(date_str: str | None) -> date | None:
    """Parse a date string like '01/24/2023' or '04/07/2025'. Returns None for 'Various' or None."""
    if not date_str or date_str.lower() == "various":
        return None
    try:
        parts = date_str.split("/")
        if len(parts) == 3:
            return date(int(parts[2]), int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        pass
    return None


def apply_cross_broker_wash_sales(tax_input: TaxInput) -> None:
    """Detect and apply cross-broker wash sales.

    For each loss sale at broker X, checks if there's a purchase of the same
    security within ±30 days at a different broker Y. If so, disallows the
    loss (or portion thereof) and adjusts the transaction's wash_sale_loss_disallowed
    and gain_or_loss in-place.

    Only detects cross-broker wash sales. Intra-broker wash sales are already
    handled by the broker's 1099-B reporting.
    """
    if len(tax_input.forms_1099_b) < 2 and not tax_input.trade_history:
        # Need multiple brokers or trade history for cross-broker wash sales
        return

    _Z = Decimal("0")

    _Z = Decimal("0")

    # Build a list of all transactions tagged with their broker index
    # We track sales (for loss detection) and acquisitions (for wash sale matching)
    sales = []  # (broker_idx, txn, ticker, sale_date, shares)
    acquisitions = []  # (broker_idx, ticker, acq_date, shares)

    for broker_idx, form in enumerate(tax_input.forms_1099_b):
        for txn in form.transactions:
            ticker = extract_ticker(txn.description)
            if not ticker:
                continue

            sale_date = parse_date(txn.date_sold)
            acq_date = parse_date(txn.date_acquired)
            shares = extract_shares(txn.description)

            if sale_date:
                sales.append((broker_idx, txn, ticker, sale_date, shares))

            # The acquisition date represents when replacement shares were bought
            # For wash sale purposes, every transaction represents both a sale AND
            # a prior acquisition. The acquisition dates from 1099-B tell us when
            # shares were purchased (which could trigger wash sales for losses at
            # other brokers).
            if acq_date and shares:
                acquisitions.append((broker_idx, ticker, acq_date, shares))

    # Add purchases from trade history (these are buy-only transactions not on 1099-B)
    # Use broker_idx = -1 to ensure they're always treated as cross-broker
    for entry in tax_input.trade_history:
        acq_date = parse_date(entry.date_acquired)
        if acq_date and entry.shares > _Z:
            acquisitions.append((-1, entry.ticker, acq_date, entry.shares))

    # Group acquisitions by ticker for fast lookup
    acq_by_ticker: dict[str, list[tuple[int, date, Decimal]]] = defaultdict(list)
    for broker_idx, ticker, acq_date, shares in acquisitions:
        acq_by_ticker[ticker].append((broker_idx, acq_date, shares))

    # For each sale at a loss, check for cross-broker wash sales
    for broker_idx, txn, ticker, sale_date, sale_shares in sales:
        # Calculate the raw loss (before any existing wash sale adjustment)
        raw_loss = txn.proceeds - txn.cost_basis
        if raw_loss >= _Z:
            # Not a loss — no wash sale possible
            continue

        # The remaining disallowable loss = total loss minus what broker already disallowed
        already_disallowed = txn.wash_sale_loss_disallowed
        remaining_loss = abs(raw_loss) - already_disallowed
        if remaining_loss <= _Z:
            # Broker already fully disallowed this loss
            continue

        # Look for cross-broker acquisitions of the same ticker within ±30 days
        cross_broker_shares = _Z
        for acq_broker_idx, acq_date, acq_shares in acq_by_ticker.get(ticker, []):
            if acq_broker_idx == broker_idx:
                # Same broker — already handled by broker's wash sale reporting
                continue
            if abs((acq_date - sale_date).days) <= 30:
                cross_broker_shares += acq_shares

        if cross_broker_shares <= _Z:
            continue

        # Calculate additional disallowed loss from cross-broker wash sale
        if sale_shares and sale_shares > _Z:
            # Partial wash sale: only disallow proportional to shares replaced
            fraction = min(cross_broker_shares / sale_shares, Decimal("1"))
            additional_disallowed = min(
                (abs(raw_loss) * fraction).quantize(Decimal("0.01")),
                remaining_loss,
            )
        else:
            # No share count available — disallow the full remaining loss
            additional_disallowed = remaining_loss

        if additional_disallowed > _Z:
            txn.wash_sale_loss_disallowed += additional_disallowed
            # Recompute gain/loss: proceeds - cost_basis + wash_sale_loss_disallowed
            txn.gain_or_loss = (
                txn.proceeds - txn.cost_basis + txn.wash_sale_loss_disallowed
            )
