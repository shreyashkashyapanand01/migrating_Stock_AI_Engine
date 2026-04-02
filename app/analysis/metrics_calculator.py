import logging
import numpy as np

logger = logging.getLogger(__name__)


def calculate_metrics(trades):
    logger.info("metrics_calculator: Started calculating trade metrics")

    try:
        profits = [t["profitLoss"] for t in trades]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p < 0]

        holding_wins = [t["holdingMinutes"] for t in trades if t["profitLoss"] > 0]
        holding_losses = [t["holdingMinutes"] for t in trades if t["profitLoss"] < 0]

        quantities = [t["quantity"] for t in trades]

        win_rate = len(wins) / len(profits) if profits else 0

        avg_win_hold = np.mean(holding_wins) if holding_wins else 0
        avg_loss_hold = np.mean(holding_losses) if holding_losses else 0

        avg_profit = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 1

        avg_rr = avg_profit / avg_loss if avg_loss != 0 else 0

        # Max Drawdown
        equity = np.cumsum(profits)
        peak = np.maximum.accumulate(equity)
        drawdown = peak - equity
        max_drawdown = np.max(drawdown) if len(drawdown) else 0

        # Loss streak frequency
        loss_streak = 0
        streaks = 0
        for p in profits:
            if p < 0:
                loss_streak += 1
            else:
                if loss_streak > 1:
                    streaks += 1
                loss_streak = 0

        loss_streak_freq = streaks / len(profits) if profits else 0

        position_variance = np.var(quantities) if quantities else 0

        logger.info("metrics_calculator: Successfully finished calculating metrics")

        return {
            "winRate": round(win_rate, 2),
            "avgWinHoldMinutes": round(avg_win_hold, 2),
            "avgLossHoldMinutes": round(avg_loss_hold, 2),
            "avgRiskReward": round(avg_rr, 2),
            "maxDrawdown": round(float(max_drawdown), 2),
            "lossStreakFrequency": round(loss_streak_freq, 2),
            "positionSizeVariance": round(float(position_variance), 2)
        }

    except Exception as e:
        logger.error(f"Error in metrics_calculator.py at calculate_metrics: Calculation failed - {str(e)}")
        # Return a zeroed-out dictionary as a safe fallback
        return {
            "winRate": 0,
            "avgWinHoldMinutes": 0,
            "avgLossHoldMinutes": 0,
            "avgRiskReward": 0,
            "maxDrawdown": 0,
            "lossStreakFrequency": 0,
            "positionSizeVariance": 0
        }