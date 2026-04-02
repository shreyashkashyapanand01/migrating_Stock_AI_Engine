import logging
from app.tools.market_data_tool import get_stock_name
import yfinance as yf

logger = logging.getLogger(__name__)


def get_sector(symbol: str):
    logger.info(f"sector_mapper: Started fetching sector for {symbol}")

    try:
        ticker_symbol = get_stock_name(symbol)

        if not ticker_symbol.endswith(".NS"):
            ticker_symbol += ".NS"
            
        logger.info(f"sector_mapper: Querying yfinance for ticker {ticker_symbol}")
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        sector = info.get("sector", "Others")

        logger.info(f"sector_mapper: Successfully mapped {symbol} to sector: {sector}")
        return sector

    except Exception as e:
        logger.error(f"Error in sector_mapper.py at get_sector: Failed for {symbol} - {str(e)}")
        return "Others"