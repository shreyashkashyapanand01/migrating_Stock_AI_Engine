import logging
import uuid
from datetime import datetime
from langgraph.graph import StateGraph, START, END

from app.state.trade_state import TradeState
from app.analysis.metrics_calculator import calculate_metrics
from app.analysis.pattern_detector import detect_patterns
from app.agents.behaviour_agent import behaviour_node

logger = logging.getLogger(__name__)


# ── Node 1 ───────────────────────────────────────────────────────────────────
def metrics_node(state: TradeState) -> dict:
    """Compute quantitative metrics from raw trade list. No LLM."""
    logger.info("trade_graph | metrics_node: Calculating trade metrics")

    trades = state.get("trades", [])

    if not trades:
        logger.warning("trade_graph | metrics_node: No trades provided")
        return {
            "metrics": {},
            "error":   "No trades provided"
        }

    try:
        metrics = calculate_metrics(trades)
        logger.info("trade_graph | metrics_node: Metrics calculated successfully")
        return {"metrics": metrics, "error": None}

    except Exception as e:
        logger.error(f"trade_graph | metrics_node: Failed - {e}")
        return {
            "metrics": {},
            "error":   "Metrics calculation failed"
        }


# ── Node 2 ───────────────────────────────────────────────────────────────────
def pattern_node(state: TradeState) -> dict:
    """Detect behavioral mistakes from computed metrics. No LLM."""
    logger.info("trade_graph | pattern_node: Detecting behavioral patterns")

    metrics = state.get("metrics", {})

    if not metrics:
        logger.warning("trade_graph | pattern_node: No metrics to analyze")
        return {"mistakes": []}

    try:
        mistakes = detect_patterns(metrics)
        logger.info(
            f"trade_graph | pattern_node: {len(mistakes)} patterns detected"
        )
        return {"mistakes": mistakes}

    except Exception as e:
        logger.error(f"trade_graph | pattern_node: Failed - {e}")
        return {"mistakes": []}


# ── Node 3 — behaviour_node is imported directly from behaviour_agent.py ─────
# (ReAct agent — see app/agents/behaviour_agent.py)


# ── Graph Assembly ────────────────────────────────────────────────────────────
def build_trade_graph():
    builder = StateGraph(TradeState)

    builder.add_node("metrics_node",   metrics_node)
    builder.add_node("pattern_node",   pattern_node)
    builder.add_node("behaviour_node", behaviour_node)

    builder.add_edge(START,            "metrics_node")
    builder.add_edge("metrics_node",   "pattern_node")
    builder.add_edge("pattern_node",   "behaviour_node")
    builder.add_edge("behaviour_node", END)

    return builder.compile(checkpointer=None)


trade_graph = build_trade_graph()


def run_trade_graph(trades: list) -> dict:
    logger.info(f"trade_graph: Starting analysis for {len(trades)} trades")

    try:
        result = trade_graph.invoke({
            "trades":      trades,
            "metrics":     {},
            "mistakes":    [],
            "risk_score":  0,
            "trader_type": "",
            "summary":     "",
            "suggestions": [],
            "error":       None
        })

        if result.get("error"):
            logger.error(
                f"trade_graph: Completed with error - {result['error']}"
            )
            return {"error": result["error"]}

        logger.info(
            f"trade_graph: Completed — "
            f"trader_type={result.get('trader_type')}"
        )

        return {
            "analysisId":  str(uuid.uuid4())[:8],
            "generatedAt": datetime.utcnow().isoformat(),
            "riskScore":   result.get("risk_score",  0),
            "traderType":  result.get("trader_type", "unknown"),
            "mistakes":    result.get("mistakes",    []),
            "metrics":     result.get("metrics",     {}),
            "summary":     result.get("summary",     ""),
            "suggestions": result.get("suggestions", [])
        }

    except Exception as e:
        logger.error(f"trade_graph: Crashed - {e}")
        return {"error": "Trade analysis failed"}