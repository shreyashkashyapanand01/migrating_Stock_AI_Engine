import logging
from app.tools.market_data_tool import fetch_latest_price, fetch_price_history

logger = logging.getLogger(__name__)


def get_market_data(symbol: str):
    logger.info(f"market_data_adapter: Getting structured market data for {symbol}")

    try:
        price = fetch_latest_price(symbol)
        history = fetch_price_history(symbol)

        if history.empty:
            logger.warning(f"market_data_adapter: No history for {symbol}")

        logger.info(f"market_data_adapter: Successfully finished fetching market data for {symbol}")
        return {
            "price": price,
            "history": history
        }

    except Exception as e:
        logger.error(f"market_data_adapter: Failed for {symbol} - {str(e)}")
        return {
            "price": 0,
            "history": None
        }