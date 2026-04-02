import logging
import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.tools.trade_tools import classify_trader_profile
from app.state.trade_state import TradeState

load_dotenv()
logger = logging.getLogger(__name__)

llm = ChatGroq(
    model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3
)

_SYSTEM_PROMPT = (
    "You are an AI trading psychologist and performance coach. "
    "You will receive a trader's computed metrics and detected behavioral mistakes. "
    "Your job is to: "
    "1) Call classify_trader_profile ONCE with the mistakes and key metrics to determine trader type and risk score. "
    "2) After receiving the classification, write a 2-line psychological summary of the trader. "
    "3) Provide exactly 3 concise, actionable coaching suggestions. "
    "Rules: Do NOT give buy/sell signals. Be educational and direct, like a coach. "
    "Return ONLY valid JSON with keys: trader_type, risk_score, summary, suggestions (list of 3 strings). "
    "No extra text, no markdown fences."
)

agent = create_react_agent(
    model=llm,
    tools=[classify_trader_profile],
    prompt=_SYSTEM_PROMPT,
)


def behaviour_node(state: TradeState) -> dict:
    logger.info("behaviour_agent: Running behaviour_node")

    metrics  = state.get("metrics", {})
    mistakes = state.get("mistakes", [])

    user_message = f"""
Trader metrics:
- Win Rate: {metrics.get("winRate")}
- Avg Win Hold Time: {metrics.get("avgWinHoldMinutes")} minutes
- Avg Loss Hold Time: {metrics.get("avgLossHoldMinutes")} minutes
- Risk Reward Ratio: {metrics.get("avgRiskReward")}
- Max Drawdown: {metrics.get("maxDrawdown")}
- Loss Streak Frequency: {metrics.get("lossStreakFrequency")}
- Position Size Variance: {metrics.get("positionSizeVariance")}

Detected behavioral mistakes: {", ".join(mistakes) if mistakes else "None"}

Call classify_trader_profile with the above data, then return your full JSON analysis.
"""

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config={"recursion_limit": 6}
        )

        last_message = result["messages"][-1].content

        if isinstance(last_message, str):
            try:
                parsed = json.loads(last_message)
                logger.info(
                    f"behaviour_agent: Completed — "
                    f"type={parsed.get('trader_type')}, "
                    f"risk={parsed.get('risk_score')}"
                )
                return {
                    "trader_type": parsed.get("trader_type", "unknown"),
                    "risk_score":  parsed.get("risk_score", 0),
                    "summary":     parsed.get("summary", ""),
                    "suggestions": parsed.get("suggestions", [])
                }
            except json.JSONDecodeError:
                pass

        # Fallback: extract from tool call result if JSON parse fails
        for message in result["messages"]:
            if hasattr(message, "name") and message.name == "classify_trader_profile":
                try:
                    tool_result = json.loads(message.content)
                    logger.warning(
                        "behaviour_agent: Falling back to tool result only"
                    )
                    return {
                        "trader_type": tool_result.get("trader_type", "unknown"),
                        "risk_score":  tool_result.get("risk_score", 50),
                        "summary": (
                            "Trading behaviour analysis could not be fully "
                            "generated. Please review metrics manually."
                        ),
                        "suggestions": [
                            "Maintain discipline in trade execution",
                            "Follow predefined risk management rules",
                            "Avoid emotional decision making"
                        ]
                    }
                except Exception:
                    pass

        raise ValueError("Could not extract valid result from agent messages")

    except Exception as e:
        logger.error(f"behaviour_agent: Failed - {e}")
        return {
            "trader_type": "unknown",
            "risk_score":  50,
            "summary": (
                "Trading behaviour analysis is currently unavailable due to an AI error."
            ),
            "suggestions": [
                "Maintain discipline in trade execution",
                "Follow predefined risk management rules",
                "Avoid emotional decision making"
            ]
        }