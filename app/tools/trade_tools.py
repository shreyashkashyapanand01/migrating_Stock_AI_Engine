import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def classify_trader_profile(
    mistakes: list,
    win_rate: float,
    avg_risk_reward: float,
    loss_streak_frequency: float,
    position_size_variance: float
) -> dict:
    """
    Classify the trader's profile based on detected behavioral mistakes and key metrics.
    Returns trader_type (disciplined / emotional / aggressive / undisciplined)
    and risk_score (0-100).
    Call this once with the detected mistakes and core metrics.
    """
    logger.info("trade_tools: classify_trader_profile called")

    try:
        # Risk score — each mistake adds 20 points, capped at 100
        risk_score = min(len(mistakes) * 20, 100)

        # Trader type — priority order matters
        if "revenge_trading" in mistakes:
            trader_type = "emotional"
        elif "inconsistent_position_size" in mistakes:
            trader_type = "aggressive"
        elif len(mistakes) == 0 and win_rate >= 0.5 and avg_risk_reward >= 1:
            trader_type = "disciplined"
        else:
            trader_type = "undisciplined"

        logger.info(
            f"trade_tools: Profile → type={trader_type}, risk_score={risk_score}"
        )

        return {
            "trader_type": trader_type,
            "risk_score":  risk_score
        }

    except Exception as e:
        logger.error(f"trade_tools: classify_trader_profile failed - {e}")
        return {
            "trader_type": "unknown",
            "risk_score":  50
        }