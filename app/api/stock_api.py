import logging
import json
import os
import redis
from fastapi import APIRouter
from app.schemas.stock_schema import StockResponse
from app.graphs.stock_graph import run_stock_graph

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Redis (graceful fallback if not available)
redis_client = None
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    logger.info("stock_api: Successfully connected to Redis.")
except Exception as e:
    logger.warning(f"stock_api: Redis not available. Caching disabled. {e}")
    redis_client = None


@router.get("/analyze-stock/{symbol}", response_model=StockResponse)
def analyze_stock(symbol: str):
    logger.info(f"stock_api: Received request for {symbol}")
    
    cache_key = f"stock_analysis:{symbol.upper()}"
    
    # 1. Check Cache
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"stock_api: Cache HIT for {symbol}. Returning instantly.")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"stock_api: Redis error during GET for {symbol} - {e}")

    # 2. Run Graph (Cache Miss)
    try:
        logger.info(f"stock_api: Cache MISS for {symbol}. Running AI Engine...")
        result = run_stock_graph(symbol)

        if "error" in result:
            logger.error(f"stock_api: Graph returned error for {symbol}")
        elif redis_client:
            # 3. Store in Cache with TTL (e.g. 2 hours = 7200 seconds)
            try:
                redis_client.setex(cache_key, 7200, json.dumps(result))
                logger.info(f"stock_api: Cached result for {symbol} successfully.")
            except Exception as e:
                logger.warning(f"stock_api: Redis error during SET for {symbol} - {e}")

        logger.info(f"stock_api: Returning freshly computed result for {symbol}")
        return result

    except Exception as e:
        logger.error(f"stock_api: Unexpected crash for {symbol} - {e}")
        return {"symbol": symbol, "error": "Internal server error"}
