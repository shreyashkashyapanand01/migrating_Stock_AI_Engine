import logging
import random
import json
from typing import List, Dict, Any
from langchain_core.tools import tool
import yfinance as yf

from app.tools.market_data_tool import get_stock_name, fetch_latest_price
from app.tools.news_tool import fetch_news

logger = logging.getLogger(__name__)

RISK_FREE_RATE = 0.06


# ── Tool 1: Fetch latest price for a single stock ────────────────────────────

@tool
def get_stock_price(symbol: str) -> str:
    """
    Fetch the latest market price for a given stock symbol.
    Returns JSON with symbol and current price.
    """
    logger.info(f"portfolio_tools | get_stock_price: Fetching price for {symbol}")
    try:
        price = fetch_latest_price(symbol)
        return json.dumps({"symbol": symbol, "price": price})
    except Exception as e:
        logger.error(f"portfolio_tools | get_stock_price: Failed for {symbol} - {e}")
        return json.dumps({"symbol": symbol, "price": 0.0})


# ── Tool 2: Get sector for a stock ───────────────────────────────────────────

@tool
def get_stock_sector(symbol: str) -> str:
    """
    Fetch the market sector for a given stock symbol using yfinance.
    Returns JSON with symbol and sector name.
    """
    logger.info(f"portfolio_tools | get_stock_sector: Fetching sector for {symbol}")
    try:
        ticker_symbol = get_stock_name(symbol)
        if not ticker_symbol.endswith(".NS"):
            ticker_symbol += ".NS"

        ticker = yf.Ticker(ticker_symbol)
        info   = ticker.info
        sector = info.get("sector", "Others")

        logger.info(f"portfolio_tools | get_stock_sector: {symbol} -> {sector}")
        return json.dumps({"symbol": symbol, "sector": sector})

    except Exception as e:
        logger.error(f"portfolio_tools | get_stock_sector: Failed for {symbol} - {e}")
        return json.dumps({"symbol": symbol, "sector": "Others"})


# ── Tool 3: Run stress test on portfolio metrics ──────────────────────────────

@tool
def run_portfolio_stress_test(total_value: float) -> str:
    """
    Run a portfolio stress test given the total portfolio value.
    Simulates a market crash (-15%) and interest rate hike (-5%) scenario.
    Returns JSON with marketCrashImpact and interestRateImpact as percentages.
    """
    logger.info(f"portfolio_tools | run_portfolio_stress_test: Running for total_value={total_value}")
    try:
        if total_value == 0:
            logger.warning("portfolio_tools | run_portfolio_stress_test: total_value is 0")
            return json.dumps({
                "marketCrashImpact":   "0%",
                "interestRateImpact":  "0%"
            })

        market_crash_value    = total_value * 0.85
        interest_rate_value   = total_value * 0.95

        market_impact   = round(((market_crash_value  - total_value) / total_value) * 100, 2)
        interest_impact = round(((interest_rate_value - total_value) / total_value) * 100, 2)

        logger.info(f"portfolio_tools | run_portfolio_stress_test: Done - market={market_impact}%, interest={interest_impact}%")
        return json.dumps({
            "marketCrashImpact":  f"{market_impact}%",
            "interestRateImpact": f"{interest_impact}%"
        })

    except Exception as e:
        logger.error(f"portfolio_tools | run_portfolio_stress_test: Failed - {e}")
        return json.dumps({
            "marketCrashImpact":  "Calculation Error",
            "interestRateImpact": "Calculation Error"
        })


# ── Tool 4: Assess overall portfolio health ───────────────────────────────────

@tool
def assess_portfolio_health(
    metrics_json:        str,
    diversification_json: str,
    stress_test_json:    str,
    sentiment_json:      str
) -> str:
    """
    Assess the overall health of a portfolio given its metrics, diversification,
    stress test results, and sentiment data.

    All arguments must be valid JSON strings.

    Returns JSON with:
    - portfolioHealthScore (0-100)
    - riskLevel ("Low" | "Moderate" | "High")
    - scoringBreakdown (dict explaining how score was derived)
    """
    logger.info("portfolio_tools | assess_portfolio_health: Assessing portfolio health")

    try:
        metrics        = json.loads(metrics_json)
        diversification = json.loads(diversification_json)
        stress_test    = json.loads(stress_test_json)
        sentiment      = json.loads(sentiment_json)

        score = 50  # base score

        # ── Metrics scoring (max +20) ────────────────────────────────────────
        sharpe = metrics.get("sharpeRatio", 0)
        if sharpe > 1.5:
            score += 20
        elif sharpe > 0.5:
            score += 10
        elif sharpe < 0:
            score -= 10

        total_return = metrics.get("totalReturn", 0)
        if total_return > 15:
            score += 10
        elif total_return > 0:
            score += 5
        elif total_return < 0:
            score -= 10

        # ── Diversification scoring (max +15) ───────────────────────────────
        div_risk = diversification.get("risk", "")
        if "Well Diversified" in div_risk:
            score += 15
        elif "High concentration" in div_risk:
            score -= 10

        # ── Stress test scoring (max +10) ────────────────────────────────────
        try:
            crash_impact = float(
                stress_test.get("marketCrashImpact", "0%").replace("%", "")
            )
            if crash_impact > -10:
                score += 10
            elif crash_impact > -20:
                score += 5
        except Exception:
            pass

        # ── Sentiment scoring (max +5) ───────────────────────────────────────
        bullish_count = sum(
            1 for s in sentiment.values()
            if isinstance(s, dict) and s.get("sentiment") == "Bullish"
        )
        bearish_count = sum(
            1 for s in sentiment.values()
            if isinstance(s, dict) and s.get("sentiment") == "Bearish"
        )
        if bullish_count > bearish_count:
            score += 5
        elif bearish_count > bullish_count:
            score -= 5

        # ── Clamp ────────────────────────────────────────────────────────────
        score = max(0, min(100, score))

        # ── Risk level ───────────────────────────────────────────────────────
        beta = metrics.get("beta", 1.0)
        volatility = metrics.get("volatility", 0)

        if beta > 1.5 or volatility > 0.3:
            risk_level = "High"
        elif beta < 0.8 and volatility < 0.15:
            risk_level = "Low"
        else:
            risk_level = "Moderate"

        logger.info(
            f"portfolio_tools | assess_portfolio_health: "
            f"score={score}, risk={risk_level}"
        )

        return json.dumps({
            "portfolioHealthScore": score,
            "riskLevel": risk_level,
            "scoringBreakdown": {
                "sharpeContribution":        sharpe,
                "returnContribution":        total_return,
                "diversificationRisk":       div_risk,
                "sentimentBullishCount":     bullish_count,
                "sentimentBearishCount":     bearish_count,
            }
        })

    except Exception as e:
        logger.error(f"portfolio_tools | assess_portfolio_health: Failed - {e}")
        return json.dumps({
            "portfolioHealthScore": 50,
            "riskLevel":            "Moderate",
            "scoringBreakdown":     {}
        })


# ── Tool 5: Fetch news headlines for sentiment ────────────────────────────────

@tool
def get_portfolio_news(symbol: str) -> str:
    """
    Fetch recent news headlines for a given stock symbol.
    Returns JSON with symbol and list of headline strings.
    """
    logger.info(f"portfolio_tools | get_portfolio_news: Fetching news for {symbol}")
    try:
        headlines = fetch_news(symbol)
        return json.dumps({
            "symbol":    symbol,
            "headlines": headlines if headlines else []
        })
    except Exception as e:
        logger.error(f"portfolio_tools | get_portfolio_news: Failed for {symbol} - {e}")
        return json.dumps({"symbol": symbol, "headlines": []})