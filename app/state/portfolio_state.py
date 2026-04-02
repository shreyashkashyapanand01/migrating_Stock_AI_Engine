from typing import TypedDict, List, Optional, Dict, Any


# ── Sub-types ────────────────────────────────────────────────────────────────

class HoldingItem(TypedDict):
    symbol:    str
    quantity:  int
    buy_price: float


class SentimentResult(TypedDict):
    sentiment:  str        # "Bullish" | "Bearish" | "Neutral"
    confidence: float      # 0.0 – 1.0


# ── Main State ───────────────────────────────────────────────────────────────

class PortfolioState(TypedDict):

    # ── Input ────────────────────────────────────────────────────────────────
    holdings:              List[HoldingItem]

    # ── metrics_node output ──────────────────────────────────────────────────
    metrics:               Dict[str, Any]      # totalInvestment, totalValue, beta …

    # ── diversification_node output ─────────────────────────────────────────
    diversification:       Dict[str, Any]      # sectorExposure, risk

    # ── stress_node output ───────────────────────────────────────────────────
    stress_test:           Dict[str, str]      # marketCrashImpact, interestRateImpact

    # ── sentiment_node output ────────────────────────────────────────────────
    # key = stock symbol,  value = SentimentResult
    sentiment:             Dict[str, SentimentResult]

    # ── decision_node output ─────────────────────────────────────────────────
    portfolio_health_score: int                # 0 – 100
    risk_level:             str                # "Low" | "Moderate" | "High"
    summary:                str
    actions:                List[str]

    # ── meta ─────────────────────────────────────────────────────────────────
    analysis_id:           Optional[str]
    generated_at:          Optional[str]
    error:                 Optional[str]