import logging

logger = logging.getLogger(__name__)


def detect_patterns(metrics):
    logger.info("pattern_detector: Started detecting behavioural patterns")

    try:
        mistakes = []

        if metrics["avgWinHoldMinutes"] < metrics["avgLossHoldMinutes"]:
            mistakes.append("cutting_winners_early")

        if metrics["lossStreakFrequency"] > 0.3:
            mistakes.append("revenge_trading")

        if metrics["positionSizeVariance"] > 50:
            mistakes.append("inconsistent_position_size")

        if metrics["avgRiskReward"] < 1:
            mistakes.append("poor_risk_reward")

        if metrics["winRate"] < 0.4:
            mistakes.append("low_win_rate")

        logger.info(f"pattern_detector: Successfully detected {len(mistakes)} behavioural patterns")
        return mistakes

    except Exception as e:
        logger.error(f"Error in pattern_detector.py at detect_patterns: Pattern detection failed - {str(e)}")
        return []