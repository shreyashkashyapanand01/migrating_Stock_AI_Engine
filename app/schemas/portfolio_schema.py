from pydantic import BaseModel
from typing import List, Dict, Any, Optional


# ── Request ──────────────────────────────────────────────────────────────────

class Holding(BaseModel):
    symbol:    str
    quantity:  int
    buy_price: float


class PortfolioAnalysisRequest(BaseModel):
    holdings: List[Holding]


# ── Response ─────────────────────────────────────────────────────────────────

class PortfolioAnalysisResponse(BaseModel):
    analysisId:            str
    generatedAt:           str
    portfolioHealthScore:  int
    riskLevel:             str
    metrics:               Dict[str, Any]
    diversification:       Dict[str, Any]
    stressTest:            Dict[str, str]
    sentiment:             Dict[str, Any]
    summary:               str
    actions:               List[str]