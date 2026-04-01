import logging
from fastapi import APIRouter
from app.schemas.scan_schema import ScanResponse
from app.graphs.scan_graph import run_scan_graph          # ← changed import

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/scan-market", response_model=ScanResponse)
def scan_market():
    logger.info("scan_api: Received request to scan the market")

    try:
        results = run_scan_graph()                         # ← changed call
        logger.info(f"scan_api: Market scan completed with {len(results)} opportunities")
        return {"opportunities": results}

    except Exception:
        logger.error("scan_api: Failed to complete market scan request")
        return {"opportunities": [], "error": "Internal server error during market scan"}