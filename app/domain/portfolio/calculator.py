from decimal import Decimal

from app.models.portfolio import Portfolio


def compute_position_metrics(
    symbol: str,
    quantity: Decimal,
    average_cost: Decimal,
    current_price: Decimal,
) -> dict:
    market_value = quantity * current_price
    cost_basis = quantity * average_cost
    unrealized_pnl = market_value - cost_basis
    pnl_pct = (
        (unrealized_pnl / cost_basis * 100).quantize(Decimal("0.01"))
        if cost_basis
        else Decimal("0")
    )

    return {
        "symbol": symbol,
        "quantity": str(quantity),
        "average_cost": str(average_cost),
        "current_price": str(current_price),
        "market_value": str(market_value.quantize(Decimal("0.01"))),
        "unrealized_pnl": str(unrealized_pnl.quantize(Decimal("0.01"))),
        "pnl_pct": str(pnl_pct),
    }


def compute_portfolio_metrics(portfolio: Portfolio, prices: dict[str, Decimal]) -> dict:
    positions = []
    total_value = Decimal("0")
    total_cost = Decimal("0")

    for position in portfolio.positions:
        current_price = prices.get(position.symbol)
        if current_price is None:
            continue

        metrics = compute_position_metrics(
            position.symbol,
            position.quantity,
            position.average_cost,
            current_price,
        )
        positions.append(metrics)

        total_value += position.quantity * current_price
        total_cost += position.quantity * position.average_cost

    total_pnl = total_value - total_cost

    return {
        "portfolio_id": str(portfolio.id),
        "total_value": str(total_value.quantize(Decimal("0.01"))),
        "total_pnl": str(total_pnl.quantize(Decimal("0.01"))),
        "positions": positions,
    }
