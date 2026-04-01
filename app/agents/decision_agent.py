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
You are an expert AI stock advisor helping a retail investor make an informed decision about {state['symbol']}.

Here is the current analysis:

Technical signals:
- Trend: {trend}
- Momentum: {momentum}
- RSI: {rsi}
- Volatility: {volatility}

Fundamental signals:
- Valuation: {valuation}
- Growth outlook: {growth}
- Profit margin: {fundamental.get('profit_margin', 'N/A')}
- Debt to equity: {fundamental.get('debt_to_equity', 'N/A')}

Recent news sentiment:
{news_analysis}

Current price: {state.get('current_price', 'N/A')}

Based on all the above, provide a structured advisor-style analysis with the following sections:

1. Overall verdict — one of: Strong Buy / Buy / Hold / Wait / Avoid. State it clearly.
2. Why — 2-3 sentences explaining the reasoning behind the verdict using the signals above.
3. Key risks — 1-2 risks the investor should be aware of before entering.
4. What to watch — 1-2 things the investor should monitor going forward (price levels, news, earnings etc).

Keep the tone like a knowledgeable friend who knows finance — clear, honest, and direct.
Do NOT use excessive disclaimers.
Do NOT write more than 150 words total.
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        summary = response.content
        logger.info(f"decision_agent: Summary generated for {state['symbol']}")
        return {"summary": summary}

    except Exception as e:
        logger.error(f"decision_agent: Failed for {state['symbol']} - {e}")
        return {"summary": "Decision summary unavailable due to an AI processing error."}