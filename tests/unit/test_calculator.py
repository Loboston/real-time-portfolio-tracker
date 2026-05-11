from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.domain.portfolio.calculator import compute_position_metrics, compute_portfolio_metrics


class TestComputePositionMetrics:
    def test_profit(self):
        result = compute_position_metrics(
            symbol="AAPL",
            quantity=Decimal("10"),
            average_cost=Decimal("150.00"),
            current_price=Decimal("180.00"),
        )
        assert result["market_value"] == "1800.00"
        assert result["unrealized_pnl"] == "300.00"
        assert result["pnl_pct"] == "20.00"

    def test_loss(self):
        result = compute_position_metrics(
            symbol="AAPL",
            quantity=Decimal("10"),
            average_cost=Decimal("180.00"),
            current_price=Decimal("150.00"),
        )
        assert result["market_value"] == "1500.00"
        assert result["unrealized_pnl"] == "-300.00"
        assert result["pnl_pct"] == "-16.67"

    def test_breakeven(self):
        result = compute_position_metrics(
            symbol="AAPL",
            quantity=Decimal("10"),
            average_cost=Decimal("150.00"),
            current_price=Decimal("150.00"),
        )
        assert result["unrealized_pnl"] == "0.00"
        assert result["pnl_pct"] == "0.00"

    def test_fractional_shares(self):
        result = compute_position_metrics(
            symbol="BTC",
            quantity=Decimal("0.5"),
            average_cost=Decimal("40000.00"),
            current_price=Decimal("50000.00"),
        )
        assert result["market_value"] == "25000.00"
        assert result["unrealized_pnl"] == "5000.00"

    def test_zero_cost_basis(self):
        result = compute_position_metrics(
            symbol="AAPL",
            quantity=Decimal("10"),
            average_cost=Decimal("0"),
            current_price=Decimal("150.00"),
        )
        assert result["pnl_pct"] == "0"

    def test_symbol_and_fields_present(self):
        result = compute_position_metrics(
            symbol="GOOGL",
            quantity=Decimal("5"),
            average_cost=Decimal("100.00"),
            current_price=Decimal("120.00"),
        )
        assert result["symbol"] == "GOOGL"
        assert result["quantity"] == "5"
        assert result["average_cost"] == "100.00"
        assert result["current_price"] == "120.00"


class TestComputePortfolioMetrics:
    def _make_portfolio(self, positions):
        portfolio = MagicMock()
        portfolio.id = "test-portfolio-id"
        portfolio.positions = positions
        return portfolio

    def _make_position(self, symbol, quantity, average_cost):
        position = MagicMock()
        position.symbol = symbol
        position.quantity = Decimal(quantity)
        position.average_cost = Decimal(average_cost)
        return position

    def test_total_value_and_pnl(self):
        portfolio = self._make_portfolio([
            self._make_position("AAPL", "10", "150.00"),
            self._make_position("GOOGL", "5", "100.00"),
        ])
        prices = {"AAPL": Decimal("180.00"), "GOOGL": Decimal("120.00")}

        result = compute_portfolio_metrics(portfolio, prices)

        assert result["total_value"] == "2400.00"   # 1800 + 600
        assert result["total_pnl"] == "400.00"      # 300 + 100
        assert len(result["positions"]) == 2

    def test_skips_positions_with_no_price(self):
        portfolio = self._make_portfolio([
            self._make_position("AAPL", "10", "150.00"),
            self._make_position("UNKNOWN", "5", "100.00"),
        ])
        prices = {"AAPL": Decimal("180.00")}

        result = compute_portfolio_metrics(portfolio, prices)

        assert len(result["positions"]) == 1
        assert result["positions"][0]["symbol"] == "AAPL"

    def test_empty_portfolio(self):
        portfolio = self._make_portfolio([])
        result = compute_portfolio_metrics(portfolio, {})

        assert result["total_value"] == "0.00"
        assert result["total_pnl"] == "0.00"
        assert result["positions"] == []

    def test_portfolio_id_in_result(self):
        portfolio = self._make_portfolio([])
        result = compute_portfolio_metrics(portfolio, {})
        assert result["portfolio_id"] == "test-portfolio-id"
