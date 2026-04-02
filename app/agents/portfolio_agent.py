import logging
import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from app.tools.portfolio_tools import assess_portfolio_health
from app.state.portfolio_state import PortfolioState

load_dotenv()
logger = logging.getLogger(__name__)

llm = ChatGroq(
    model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3
)

_SYSTEM_PROMPT = (
    "You are an expert AI Portfolio Advisor and Risk Manager. "
    "You will receive a portfolio's computed metrics, diversification analysis, "
    "stress test results, and sentiment data. "
    "Your job is to: "
    "1) Call assess_portfolio_health ONCE with all four data inputs as JSON strings "
    "   to get the health score and risk level. "
    "2) After receiving the assessment, write a professional 2-3 line portfolio summary. "
    "3) Provide exactly 3-5 concise, actionable portfolio improvement suggestions. "
    "Rules: Do NOT give specific buy/sell signals for individual stocks. "
    "Be professional, data-driven, and direct like a senior financial advisor. "
    "Return ONLY valid JSON with keys: "
    "portfolioHealthScore (int), riskLevel (string), summary (string), actions (list of strings). "
    "No extra text, no markdown fences."
)

agent = create_react_agent(
    model=llm,
    tools=[assess_portfolio_health],
    prompt=_SYSTEM_PROMPT,
)


def decision_node(state: PortfolioState) -> dict:
    """
    LangGraph node — calls the portfolio advisor agent to generate
    health score, risk level, summary and actionable suggestions.
    Follows the exact same pattern as behaviour_node in behaviour_agent.py.
    """
    logger.info("portfolio_agent | decision_node: Running portfolio decision")

    metrics         = state.get("metrics",         {})
    diversification = state.get("diversification", {})
    stress_test     = state.get("stress_test",     {})
    sentiment       = state.get("sentiment",       {})

    user_message = f"""
Portfolio Data for Analysis:

Metrics:
- Total Investment: {metrics.get("totalInvestment")}
- Total Value:      {metrics.get("totalValue")}
- Total Return:     {metrics.get("totalReturn")}%
- Beta:             {metrics.get("beta")}
- Sharpe Ratio:     {metrics.get("sharpeRatio")}
- Volatility:       {metrics.get("volatility")}

Diversification:
- Sector Exposure: {diversification.get("sectorExposure")}
- Risk:            {diversification.get("risk")}

Stress Test:
- Market Crash Impact:    {stress_test.get("marketCrashImpact")}
- Interest Rate Impact:   {stress_test.get("interestRateImpact")}

Sentiment per stock: {sentiment}

Call assess_portfolio_health with the above data as JSON strings, then return your full JSON analysis.
"""

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config={"recursion_limit": 6}
        )

        last_message = result["messages"][-1].content

        # ── Primary parse: last message is valid JSON ─────────────────────
        if isinstance(last_message, str):
            try:
                parsed = json.loads(last_message)
                logger.info(
                    f"portfolio_agent | decision_node: Completed — "
                    f"score={parsed.get('portfolioHealthScore')}, "
                    f"risk={parsed.get('riskLevel')}"
                )
                return {
                    "portfolio_health_score": int(parsed.get("portfolioHealthScore", 50)),
                    "risk_level":             parsed.get("riskLevel", "Moderate"),
                    "summary":                parsed.get("summary", ""),
                    "actions":                parsed.get("actions", [])
                }
            except json.JSONDecodeError:
                pass

        # ── Fallback: extract from tool result if JSON parse fails ────────
        for message in result["messages"]:
            if hasattr(message, "name") and message.name == "assess_portfolio_health":
                try:
                    tool_result = json.loads(message.content)
                    logger.warning(
                        "portfolio_agent | decision_node: Falling back to tool result only"
                    )
                    return {
                        "portfolio_health_score": int(
                            tool_result.get("portfolioHealthScore", 50)
                        ),
                        "risk_level": tool_result.get("riskLevel", "Moderate"),
                        "summary": (
                            "Portfolio analysis could not be fully generated. "
                            "Please review metrics manually."
                        ),
                        "actions": [
                            "Review portfolio diversification",
                            "Monitor high-risk positions",
                            "Rebalance sector allocations if needed"
                        ]
                    }
                except Exception:
                    pass

        raise ValueError("Could not extract valid result from agent messages")

    except Exception as e:
        logger.error(f"portfolio_agent | decision_node: Failed - {e}")
        return {
            "portfolio_health_score": 50,
            "risk_level":             "Moderate",
            "summary":                "Portfolio analysis is currently unavailable due to an AI error.",
            "actions": [
                "Review portfolio diversification",
                "Monitor high-risk positions",
                "Rebalance sector allocations if needed"
            ]
        }