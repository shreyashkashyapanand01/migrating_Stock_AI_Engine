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

    technical_data = state.get("technical", {})
    news_data = state.get("news", {})
    fundamental_data = state.get("fundamental", {})

    # --- Quantitative Scoring Layer ---
    tech_score = 0
    # Technical weights
    if technical_data.get("trend") == "bullish": tech_score += 40
    elif technical_data.get("trend") == "bearish": tech_score -= 40
    
    if technical_data.get("momentum") == "strong": tech_score += 30
    elif technical_data.get("momentum") == "weak": tech_score -= 30
    
    if technical_data.get("rsi") == "oversold": tech_score += 30
    elif technical_data.get("rsi") == "overbought": tech_score -= 30

    funda_score = 0
    # Fundamental weights
    if fundamental_data.get("valuation") == "undervalued": funda_score += 50
    elif fundamental_data.get("valuation") == "overvalued": funda_score -= 50
    
    if fundamental_data.get("growth") == "strong growth": funda_score += 50
    elif fundamental_data.get("growth") == "declining growth": funda_score -= 50

    # News sentiment (basic heuristic)
    news_analysis = news_data.get("analysis", "No news sentiment available.")
    news_score = 0
    if "positive" in news_analysis.lower() or "bullish" in news_analysis.lower(): news_score = 70
    elif "negative" in news_analysis.lower() or "bearish" in news_analysis.lower(): news_score = 30
    else: news_score = 50

    overall_score = (tech_score * 0.4) + (funda_score * 0.4) + (news_score * 0.2)

    prompt = f"""
You are an expert AI stock advisor helping a retail investor make an informed decision about {state['symbol']}.

Here is the current analysis:

Technical Analysis (Calculated Score: {tech_score}/100):
- Trend: {technical_data.get("trend", "unknown")}
- Momentum: {technical_data.get("momentum", "unknown")}
- RSI: {technical_data.get("rsi", "unknown")}
- Volatility: {technical_data.get("volatility", "unknown")}

Fundamental Analysis (Calculated Score: {funda_score}/100):
- Valuation: {fundamental_data.get("valuation", "unknown")}
- Growth outlook: {fundamental_data.get("growth", "unknown")}
- Profit margin: {fundamental_data.get('profit_margin', 'N/A')}
- Debt to equity: {fundamental_data.get('debt_to_equity', 'N/A')}

News Sentiment Score: {news_score}/100
Weighted Aggregated Score: {overall_score:.2f} (Scale: -100 to 100)

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