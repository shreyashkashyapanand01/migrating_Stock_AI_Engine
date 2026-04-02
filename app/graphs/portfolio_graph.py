import uuid
import logging
from datetime import datetime
from langgraph.graph import StateGraph, START, END

from app.state.portfolio_state import PortfolioState
from app.analysis.portfolio_metrics_calculator import calculate_portfolio_metrics
from app.analysis.diversification_analyzer import analyze_diversification
#from app.tools.market_data_adapter import get_market_data
from app.tools.market_data_adaptor import get_market_data
from app.agents.sentiment_agent import sentiment_node
from app.agents.portfolio_agent import decision_node

logger = logging.getLogger(__name__)


# ── Node 1: Metrics ──────────────────────────────────────────────────────────

def metrics_node(state: PortfolioState) -> dict:
    """
    Calculate portfolio financial metrics for all holdings.
    Uses portfolio_metrics_calculator (pure utility — no LLM needed here).
    """
    logger.info("portfolio_graph | metrics_node: Calculating portfolio metrics")

    holdings = state.get("holdings", [])

    if not holdings:
        logger.warning("portfolio_graph | metrics_node: No holdings provided")
        return {
            "metrics": {
                "totalInvestment": 0,
                "totalValue":      0,
                "totalReturn":     0,
                "beta":            1.0,
                "sharpeRatio":     0,
                "volatility":      0
            },
            "error": "No holdings provided"
        }

    try:
        #metrics = calculate_portfolio_metrics(holdings, get_market_data)
        
        class _HoldingProxy:
            def __init__(self, h):
                self.symbol    = h["symbol"]
                self.quantity  = h["quantity"]
                self.buy_price = h["buy_price"]

        proxies = [_HoldingProxy(h) for h in holdings]
        metrics = calculate_portfolio_metrics(proxies, get_market_data)
                
        logger.info(
            f"portfolio_graph | metrics_node: Done — "
            f"totalValue={metrics.get('totalValue')}"
        )
        return {"metrics": metrics, "error": None}

    except Exception as e:
        logger.error(f"portfolio_graph | metrics_node: Failed - {e}")
        return {
            "metrics": {
                "totalInvestment": 0,
                "totalValue":      0,
                "totalReturn":     0,
                "beta":            1.0,
                "sharpeRatio":     0,
                "volatility":      0
            },
            "error": "Metrics calculation failed"
        }


# ── Node 2: Diversification ──────────────────────────────────────────────────

def diversification_node(state: PortfolioState) -> dict:
    """
    Analyze sector diversification of the portfolio.
    Calls analyze_diversification which internally uses
    get_stock_sector tool via sector_mapper.
    """
    logger.info("portfolio_graph | diversification_node: Analyzing diversification")

    holdings = state.get("holdings", [])

    if not holdings:
        logger.warning("portfolio_graph | diversification_node: No holdings")
        return {"diversification": {"sectorExposure": {}, "risk": "No holdings"}}

    try:
        # Convert TypedDict holdings to Holding-like objects expected by analyzer
        class _HoldingProxy:
            def __init__(self, h):
                self.symbol    = h["symbol"]
                self.quantity  = h["quantity"]
                self.buy_price = h["buy_price"]

        proxies        = [_HoldingProxy(h) for h in holdings]
        diversification = analyze_diversification(proxies)

        logger.info(
            f"portfolio_graph | diversification_node: Done — "
            f"risk={diversification.get('risk')}"
        )
        return {"diversification": diversification}

    except Exception as e:
        logger.error(f"portfolio_graph | diversification_node: Failed - {e}")
        return {
            "diversification": {
                "sectorExposure": {},
                "risk":           "Error during analysis"
            }
        }


# ── Node 3: Stress Test ──────────────────────────────────────────────────────

def stress_node(state: PortfolioState) -> dict:
    """
    Run stress test using the portfolio total value from metrics.
    Calls run_portfolio_stress_test tool directly (no LLM needed).
    """
    logger.info("portfolio_graph | stress_node: Running stress test")

    metrics     = state.get("metrics", {})
    total_value = metrics.get("totalValue", 0)

    try:
        import json
        from app.tools.portfolio_tools import run_portfolio_stress_test

        # Call the tool's underlying function directly (no agent needed here)
        raw    = run_portfolio_stress_test.invoke({"total_value": total_value})
        result = json.loads(raw)

        logger.info(
            f"portfolio_graph | stress_node: Done — "
            f"marketCrashImpact={result.get('marketCrashImpact')}"
        )
        return {"stress_test": result}

    except Exception as e:
        logger.error(f"portfolio_graph | stress_node: Failed - {e}")
        return {
            "stress_test": {
                "marketCrashImpact":  "0%",
                "interestRateImpact": "0%"
            }
        }


# ── Node 4: Sentiment  →  imported from sentiment_agent.py ──────────────────
# sentiment_node(state) -> {"sentiment": {symbol: {sentiment, confidence}}}


# ── Node 5: Decision   →  imported from portfolio_agent.py ──────────────────
# decision_node(state) -> {portfolio_health_score, risk_level, summary, actions}


# ── Node 6: Finalizer ────────────────────────────────────────────────────────

def finalizer_node(state: PortfolioState) -> dict:
    """
    Stamp analysis ID and timestamp onto the completed state.
    This keeps meta-data concerns out of the agent.
    """
    logger.info("portfolio_graph | finalizer_node: Stamping analysis metadata")
    return {
        "analysis_id":  str(uuid.uuid4()),
        "generated_at": datetime.utcnow().isoformat()
    }


# ── Graph Assembly ───────────────────────────────────────────────────────────

def build_portfolio_graph():
    builder = StateGraph(PortfolioState)

    # Register nodes
    builder.add_node("metrics_node",         metrics_node)
    builder.add_node("diversification_node", diversification_node)
    builder.add_node("stress_node",          stress_node)
    builder.add_node("sentiment_node",       sentiment_node)
    builder.add_node("decision_node",        decision_node)
    builder.add_node("finalizer_node",       finalizer_node)

    # Linear pipeline — each stage feeds the next
    # metrics and diversification can run independently but stress depends
    # on metrics, so we keep it strictly linear for simplicity and debuggability
    builder.add_edge(START,                  "metrics_node")
    builder.add_edge("metrics_node",         "diversification_node")
    builder.add_edge("diversification_node", "stress_node")
    builder.add_edge("stress_node",          "sentiment_node")
    builder.add_edge("sentiment_node",       "decision_node")
    builder.add_edge("decision_node",        "finalizer_node")
    builder.add_edge("finalizer_node",       END)

    return builder.compile(checkpointer=None)


portfolio_graph = build_portfolio_graph()


# ── Public entry point (called by portfolio_api.py) ─────────────────────────

def run_portfolio_graph(holdings: list) -> dict:
    """
    Entry point — converts holdings list to initial state and runs the graph.
    Returns the final result dict ready for the API response.
    """
    logger.info(
        f"portfolio_graph: Starting portfolio analysis for "
        f"{len(holdings)} holdings"
    )

    # Normalize holdings to plain dicts (handles both Pydantic models and dicts)
    normalized = []
    for h in holdings:
        if hasattr(h, "model_dump"):
            normalized.append(h.model_dump())   # Pydantic v2
        elif hasattr(h, "dict"):
            normalized.append(h.dict())          # Pydantic v1
        else:
            normalized.append(dict(h))

    initial_state: PortfolioState = {
        "holdings":              normalized,
        "metrics":               {},
        "diversification":       {},
        "stress_test":           {},
        "sentiment":             {},
        "portfolio_health_score": 0,
        "risk_level":            "",
        "summary":               "",
        "actions":               [],
        "analysis_id":           None,
        "generated_at":          None,
        "error":                 None
    }

    try:
        result = portfolio_graph.invoke(initial_state)

        if result.get("error") and not result.get("metrics", {}).get("totalValue"):
            logger.error(
                f"portfolio_graph: Completed with error - {result['error']}"
            )

        logger.info(
            f"portfolio_graph: Completed — "
            f"score={result.get('portfolio_health_score')}, "
            f"risk={result.get('risk_level')}"
        )

        return {
            "analysisId":            result.get("analysis_id",           ""),
            "generatedAt":           result.get("generated_at",          ""),
            "portfolioHealthScore":  result.get("portfolio_health_score", 50),
            "riskLevel":             result.get("risk_level",            "Moderate"),
            "metrics":               result.get("metrics",               {}),
            "diversification":       result.get("diversification",       {}),
            "stressTest":            result.get("stress_test",           {}),
            "sentiment":             result.get("sentiment",             {}),
            "summary":               result.get("summary",               ""),
            "actions":               result.get("actions",               [])
        }

    except Exception as e:
        logger.error(f"portfolio_graph: Crashed - {e}")
        return {
            "analysisId":           str(uuid.uuid4()),
            "generatedAt":          datetime.utcnow().isoformat(),
            "portfolioHealthScore": 50,
            "riskLevel":            "Moderate",
            "metrics":              {},
            "diversification":      {},
            "stressTest":           {},
            "sentiment":            {},
            "summary":              "Portfolio analysis failed due to an internal error.",
            "actions":              ["Review portfolio manually"]
        }