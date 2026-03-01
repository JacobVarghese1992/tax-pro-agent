"""Pytest fixtures for tax calculation tests."""

import pytest

from tests.fixtures.sample_data import (
    make_capital_loss,
    make_high_income,
    make_self_employed,
    make_simple_w2_only,
    make_w2_plus_investments,
)


@pytest.fixture
def simple_w2_input():
    return make_simple_w2_only()


@pytest.fixture
def investment_input():
    return make_w2_plus_investments()


@pytest.fixture
def self_employed_input():
    return make_self_employed()


@pytest.fixture
def high_income_input():
    return make_high_income()


@pytest.fixture
def capital_loss_input():
    return make_capital_loss()
