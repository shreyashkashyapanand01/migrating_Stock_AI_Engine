import logging
from fastapi import APIRouter
from app.schemas.stock_schema import StockResponse
from app.graphs.stock_graph import run_stock_graph

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analyze-stock/{symbol}", response_model=StockResponse)
def analyze_stock(symbol: str):
    logger.info(f"stock_api: Received request for {symbol}")

    try:
        result = run_stock_graph(symbol)

        if "error" in result:
            logger.error(f"stock_api: Graph returned error for {symbol}")

        logger.info(f"stock_api: Returning result for {symbol}")
        return result

    except Exception:
        logger.error(f"stock_api: Unexpected crash for {symbol}")
        return {"symbol": symbol, "error": "Internal server error"}
