import logging
from fastapi import APIRouter
from app.schemas.portfolio_schema import PortfolioAnalysisRequest, PortfolioAnalysisResponse
from app.graphs.portfolio_graph import run_portfolio_graph          # ← changed import

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/portfolio-analyze", response_model=PortfolioAnalysisResponse)
def analyze_portfolio(request: PortfolioAnalysisRequest):
    logger.info(
        f"portfolio_api: Received portfolio analysis request "
        f"with {len(request.holdings)} holdings"
    )

    try:
        result = run_portfolio_graph(request.holdings)              # ← changed call
        logger.info("portfolio_api: Successfully completed portfolio analysis request")
        return result

    except Exception:
        logger.error("portfolio_api: Failed to complete portfolio analysis request")
        return {
            "analysisId":           "",
            "generatedAt":          "",
            "portfolioHealthScore": 50,
            "riskLevel":            "Moderate",
            "metrics":              {},
            "diversification":      {},
            "stressTest":           {},
            "sentiment":            {},
            "summary":              "Portfolio analysis failed.",
            "actions":              ["Review portfolio manually"]
        }