import logging
from langgraph.graph import StateGraph, START, END

from app.state.scan_state import ScanState
from app.data.universe_providers.gainer_provider import fetch_top_sector_performers
from app.graphs.stock_graph import run_stock_graph
from app.scoring.opportunity_scorer import score_opportunity

logger = logging.getLogger(__name__)


# ── Node 1 ──────────────────────────────────────────────────────────────────
def universe_node(state: ScanState) -> dict:
    """Fetch the top sector performers from NSE as scan candidates."""
    logger.info("scan_graph | universe_node: Fetching top sector performers")

    try:
        candidates = fetch_top_sector_performers()

        if not candidates:
            logger.warning("scan_graph | universe_node: No candidates returned")
            return {"candidates": [], "error": "No candidates fetched from NSE"}

        logger.info(f"scan_graph | universe_node: {len(candidates)} candidates fetched")
        return {"candidates": candidates, "error": None}

    except Exception as e:
        logger.error(f"scan_graph | universe_node: Failed - {e}")
        return {"candidates": [], "error": "Universe fetch failed"}


# ── Node 2 ──────────────────────────────────────────────────────────────────
def analysis_node(state: ScanState) -> dict:
    """Run stock_graph on each candidate to get full analysis."""
    logger.info("scan_graph | analysis_node: Starting per-stock analysis")

    candidates = state.get("candidates", [])

    if not candidates:
        logger.warning("scan_graph | analysis_node: No candidates to analyze")
        return {"opportunities": []}

    analyzed = []

    for stock in candidates:
        symbol = stock["symbol"]

        try:
            logger.info(f"scan_graph | analysis_node: Analyzing {symbol}")
            result = run_stock_graph(symbol)

            if result.get("error"):
                logger.warning(f"scan_graph | analysis_node: Skipping {symbol} - graph returned error")
                continue

            # Attach metadata needed downstream
            result["_sector"]    = stock["sector"]
            result["_perChange"] = stock["perChange"]

            analyzed.append(result)

        except Exception as e:
            logger.error(f"scan_graph | analysis_node: Failed for {symbol} - {e}")
            continue

    logger.info(f"scan_graph | analysis_node: {len(analyzed)} stocks analyzed successfully")
    return {"analyzed": analyzed}


# ── Node 3 ──────────────────────────────────────────────────────────────────
def scoring_node(state: ScanState) -> dict:
    """Score each analyzed stock using rule-based opportunity scorer."""
    logger.info("scan_graph | scoring_node: Scoring analyzed stocks")

    analyzed = state.get("analyzed", [])

    if not analyzed:
        logger.warning("scan_graph | scoring_node: No analyzed stocks to score")
        return {"opportunities": []}

    opportunities = []

    for result in analyzed:
        symbol     = result["symbol"]
        sector     = result["_sector"]
        per_change = result["_perChange"]

        try:
            ai_score      = score_opportunity(result)
            momentum      = per_change
            final_score   = ai_score + (momentum / 10)

            opportunities.append({
                "symbol":   symbol,
                "sector":   sector,
                "score":    round(final_score, 2),
                "momentum": round(momentum, 2),
                "summary":  result.get("summary", "")
            })

            logger.info(f"scan_graph | scoring_node: {symbol} scored {round(final_score, 2)}")

        except Exception as e:
            logger.error(f"scan_graph | scoring_node: Failed to score {symbol} - {e}")
            continue

    logger.info(f"scan_graph | scoring_node: {len(opportunities)} stocks scored")
    return {"opportunities": opportunities}


# ── Node 4 ──────────────────────────────────────────────────────────────────
def ranking_node(state: ScanState) -> dict:
    """Sort opportunities by score descending."""
    logger.info("scan_graph | ranking_node: Ranking opportunities")

    opportunities = state.get("opportunities", [])

    ranked = sorted(opportunities, key=lambda x: x["score"], reverse=True)

    logger.info(f"scan_graph | ranking_node: Final ranked list has {len(ranked)} opportunities")
    return {"opportunities": ranked}


# ── Graph Assembly ───────────────────────────────────────────────────────────
def build_scan_graph():
    builder = StateGraph(ScanState)

    builder.add_node("universe_node", universe_node)
    builder.add_node("analysis_node", analysis_node)
    builder.add_node("scoring_node",  scoring_node)
    builder.add_node("ranking_node",  ranking_node)

    builder.add_edge(START,            "universe_node")
    builder.add_edge("universe_node",  "analysis_node")
    builder.add_edge("analysis_node",  "scoring_node")
    builder.add_edge("scoring_node",   "ranking_node")
    builder.add_edge("ranking_node",   END)

    return builder.compile(checkpointer=None)


scan_graph = build_scan_graph()


def run_scan_graph() -> list:
    logger.info("scan_graph: Starting market scan")

    try:
        result = scan_graph.invoke({
            "candidates":    [],
            "analyzed":      [],
            "opportunities": [],
            "error":         None
        })

        if result.get("error"):
            logger.error(f"scan_graph: Completed with error - {result['error']}")
            return []

        opportunities = result.get("opportunities", [])
        logger.info(f"scan_graph: Completed successfully with {len(opportunities)} opportunities")
        return opportunities

    except Exception as e:
        logger.error(f"scan_graph: Crashed - {e}")
        return []