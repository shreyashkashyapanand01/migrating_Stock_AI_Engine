import logging
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from app.tools.portfolio_tools import get_portfolio_news
from app.state.portfolio_state import PortfolioState

load_dotenv()
logger = logging.getLogger(__name__)

llm = ChatGroq(
    model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

_SYSTEM_PROMPT = (
    "You are a financial news sentiment analyst. "
    "Call get_portfolio_news ONCE with the stock symbol to fetch headlines. "
    "After receiving the headlines, classify the overall sentiment. "
    "Return ONLY valid JSON with exactly these keys: "
    "'sentiment' (one of: Bullish, Bearish, Neutral) and "
    "'confidence' (a float between 0.0 and 1.0). "
    "Do NOT call any tool more than once. "
    "No extra text, no markdown fences."
)

agent = create_react_agent(
    model=llm,
    tools=[get_portfolio_news],
    prompt=_SYSTEM_PROMPT,
)


# ── Single symbol sentiment ───────────────────────────────────────────────────

def _analyze_single_symbol(symbol: str) -> tuple[str, dict]:
    """
    Run the sentiment agent for one stock symbol.
    Returns a (symbol, sentiment_result) tuple.
    Industry practice: keep per-symbol logic isolated so it can run concurrently.
    """
    logger.info(f"sentiment_agent: Analyzing sentiment for {symbol}")

    try:
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Fetch news for '{symbol}' using the tool, "
                            f"then return sentiment JSON."
                        )
                    }
                ]
            },
            config={"recursion_limit": 4}
        )

        last_message = result["messages"][-1].content

        # ── Primary parse: last message is valid JSON ─────────────────────
        if isinstance(last_message, str):
            try:
                parsed = json.loads(last_message)
                sentiment  = parsed.get("sentiment",  "Neutral")
                confidence = round(float(parsed.get("confidence", 0.5)), 2)
                logger.info(
                    f"sentiment_agent: {symbol} -> {sentiment} ({confidence})"
                )
                return symbol, {"sentiment": sentiment, "confidence": confidence}
            except (json.JSONDecodeError, ValueError):
                pass

        # ── Fallback: extract from tool result message ─────────────────────
        for message in result["messages"]:
            if hasattr(message, "name") and message.name == "get_portfolio_news":
                logger.warning(
                    f"sentiment_agent: Falling back to tool message for {symbol}"
                )
                return symbol, {"sentiment": "Neutral", "confidence": 0.5}

        logger.warning(f"sentiment_agent: No valid result for {symbol}, using default")
        return symbol, {"sentiment": "Neutral", "confidence": 0.5}

    except Exception as e:
        logger.error(f"sentiment_agent: Crashed for {symbol} - {e}")
        return symbol, {"sentiment": "Neutral", "confidence": 0.5}


# ── Node: runs all symbols concurrently ──────────────────────────────────────

def sentiment_node(state: PortfolioState) -> dict:
    """
    LangGraph node — runs sentiment analysis for every holding in parallel.
    Industry practice: use ThreadPoolExecutor for I/O-bound LLM calls
    to avoid blocking on sequential per-symbol API round trips.
    """
    holdings = state.get("holdings", [])

    if not holdings:
        logger.warning("sentiment_agent | sentiment_node: No holdings, skipping")
        return {"sentiment": {}}

    symbols = [h["symbol"] for h in holdings]
    logger.info(
        f"sentiment_agent | sentiment_node: "
        f"Running sentiment for {len(symbols)} symbols concurrently"
    )

    sentiment_map: dict = {}

    # Concurrency capped at 5 to respect Groq rate limits
    max_workers = min(5, len(symbols))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_analyze_single_symbol, symbol): symbol
            for symbol in symbols
        }
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                sym, result = future.result()
                sentiment_map[sym] = result
            except Exception as e:
                logger.error(
                    f"sentiment_agent | sentiment_node: "
                    f"Unexpected error for {symbol} - {e}"
                )
                sentiment_map[symbol] = {"sentiment": "Neutral", "confidence": 0.5}

    logger.info(
        f"sentiment_agent | sentiment_node: "
        f"Completed sentiment for {len(sentiment_map)} symbols"
    )
    return {"sentiment": sentiment_map}