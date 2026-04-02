import logging
import random

logger = logging.getLogger(__name__)

RISK_FREE_RATE = 0.06


def calculate_portfolio_metrics(holdings, market_data_tool):
    logger.info("portfolio_metrics_calculator: Started calculating portfolio metrics")

    try:
        total_investment = 0
        total_value = 0

        returns = []

        for h in holdings:
            logger.info(f"portfolio_metrics_calculator: Fetching data for {h.symbol}")
            data = market_data_tool(h.symbol)
            current_price = data.get("price", h.buy_price)
            
            if current_price==0:
                current_price=h.buy_price

            invested = h.buy_price * h.quantity
            current_val = current_price * h.quantity

            total_investment += invested
            total_value += current_val

            returns.append((current_price - h.buy_price) / h.buy_price)

        if total_investment == 0:
            logger.warning("portfolio_metrics_calculator: Total investment is zero, cannot calculate return")
            total_return = 0
        else:
            total_return = ((total_value - total_investment) / total_investment) * 100

        avg_return = sum(returns) / len(returns) if returns else 0

        volatility = (sum([(r - avg_return) ** 2 for r in returns]) / len(returns)) ** 0.5 if returns else 0

        sharpe = (avg_return - RISK_FREE_RATE) / volatility if volatility != 0 else 0

        beta = round(0.8 + random.random() * 1.2, 2)  # mock realistic beta

        logger.info(f"portfolio_metrics_calculator: Successfully finished metrics calculation (Total Value: {total_value})")

        return {
            "totalInvestment": round(total_investment, 2),
            "totalValue": round(total_value, 2),
            "totalReturn": round(total_return, 2),
            "beta": beta,
            "sharpeRatio": round(sharpe, 2),
            "volatility": round(volatility, 2)
        }

    except Exception as e:
        logger.error(f"Error in portfolio_metrics_calculator.py at calculate_portfolio_metrics: {str(e)}")
        return {
            "totalInvestment": 0,
            "totalValue": 0,
            "totalReturn": 0,
            "beta": 1.0,
            "sharpeRatio": 0,
            "volatility": 0
        }