import logging
import csv
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.trade_schema import TradeAnalysisRequest
from app.graphs.trade_graph import run_trade_graph

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze-trades")
def analyze_trades(request: TradeAnalysisRequest):
    """Accepts JSON trade list and runs the agentic trade graph."""
    logger.info("trade_api: Received JSON trade analysis request")

    try:
        trades = [t.dict() for t in request.trades]
        logger.info(
            f"trade_api: Processing {len(trades)} trades through graph"
        )

        result = run_trade_graph(trades)

        if "error" in result:
            logger.error(
                f"trade_api: Graph returned error - {result.get('error')}"
            )
        else:
            logger.info("trade_api: JSON analysis completed successfully")

        return result

    except Exception as e:
        logger.error(f"trade_api: Unexpected error - {str(e)}")
        return {"error": "Internal server error"}


@router.post("/upload-trades")
async def upload_trades(file: UploadFile = File(...)):
    """
    Accepts a CSV file of trades.
    Parses it into the same trade dict format, then runs the same graph.
    Expected CSV columns (case-insensitive):
      symbol, entry_price, exit_price, quantity, type, side,
      holdingMinutes, profitLoss
    """
    logger.info(
        f"trade_api: Received CSV upload - filename={file.filename}"
    )

    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only .csv files are accepted"
        )

    try:
        contents = await file.read()
        decoded  = contents.decode("utf-8")
        reader   = csv.DictReader(io.StringIO(decoded))

        # Normalize headers to lowercase for safety
        trades = []
        for row in reader:
            normalized = {k.strip().lower(): v.strip() for k, v in row.items()}
            trades.append({
                "symbol":         normalized.get("symbol", ""),
                "entry_price":    float(normalized.get("entry_price", 0)),
                "exit_price":     float(normalized.get("exit_price", 0)),
                "quantity":       int(normalized.get("quantity", 0)),
                "type":           normalized.get("type", ""),
                "side":           normalized.get("side", ""),
                "holdingMinutes": float(normalized.get("holdingminutes", 0)),
                "profitLoss":     float(normalized.get("profitloss", 0))
            })

        if not trades:
            raise HTTPException(
                status_code=400,
                detail="CSV file is empty or has no valid rows"
            )

        logger.info(
            f"trade_api: Parsed {len(trades)} trades from CSV, "
            f"running graph"
        )

        result = run_trade_graph(trades)

        if "error" in result:
            logger.error(
                f"trade_api: Graph returned error for CSV - {result.get('error')}"
            )
        else:
            logger.info("trade_api: CSV analysis completed successfully")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"trade_api: CSV processing failed - {str(e)}")
        return {"error": "CSV processing failed"}