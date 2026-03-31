import logging
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.state.stock_state import StockState

load_dotenv()

logger = logging.getLogger(__name__)

llm = ChatGroq(
    model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3
)


def decision_node(state: StockState) -> dict:
    logger.info(f"decision_agent: Running for {state['symbol']}")

    technical   = state.get("technical", {})
    news        = state.get("news", {})
    fundamental = state.get("fundamental", {})

    trend          = technical.get("trend", "unknown")
    momentum       = technical.get("momentum", "unknown")
    rsi            = technical.get("rsi", "unknown")
    volatility     = technical.get("volatility", "unknown")
    news_analysis  = news.get("analysis", "No news sentiment available.")
    valuation      = fundamental.get("valuation", "unknown")
    growth         = fundamental.get("growth", "unknown")

    prompt = f"""
You are an AI trading mentor.

Technical signals:
Trend: {trend}
Momentum: {momentum}
RSI condition: {rsi}
Volatility: {volatility}

Fundamental signals:
Valuation: {valuation}
Growth outlook: {growth}

Recent news sentiment:
{news_analysis}

Explain the overall market condition in 2 short concise sentences.
Do NOT give buy/sell signals.
Do NOT write long paragraphs.
Focus on concise and educational reasoning.
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        summary = response.content
        logger.info(f"decision_agent: Summary generated for {state['symbol']}")
        return {"summary": summary}

    except Exception as e:
        logger.error(f"decision_agent: Failed for {state['symbol']} - {e}")
        return {"summary": "Decision summary unavailable due to an AI processing error."}