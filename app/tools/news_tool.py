import logging
import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

logger = logging.getLogger(__name__)
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def fetch_news(symbol: str) -> list:
    logger.info(f"news_tool: Fetching web news for {symbol}")

    query = f"{symbol} stock news India NSE latest financial"

    try:
        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_domains=[
                "economictimes.indiatimes.com",
                "moneycontrol.com",
                "livemint.com",
                "business-standard.com",
                "financialexpress.com",
                "ndtvprofit.com",
                "reuters.com",
                "bloomberg.com"
            ]
        )

        results = response.get("results", [])

        headlines = []
        for r in results:
            title = r.get("title", "").strip()
            snippet = r.get("content", "").strip()
            if title:
                headlines.append(f"{title} — {snippet[:120]}" if snippet else title)

        logger.info(f"news_tool: Retrieved {len(headlines)} results for {symbol}")
        return headlines

    except Exception as e:
        logger.error(f"news_tool: Tavily search failed for {symbol} - {e}")
        return []