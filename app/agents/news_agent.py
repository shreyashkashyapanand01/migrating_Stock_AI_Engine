import logging
import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.tools.stock_tools import get_news_headlines
from app.state.stock_state import StockState

load_dotenv()
logger = logging.getLogger(__name__)

llm = ChatGroq(
    model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

agent = create_react_agent(
    model=llm,
    tools=[get_news_headlines],
    prompt=(
        "You are a financial news analyst. "
        "Call get_news_headlines ONCE with the stock symbol. "
        "After receiving the headlines, analyze sentiment and return ONLY a JSON with: "
        "'headlines' (list of strings) and 'analysis' (1-2 sentence sentiment summary). "
        "Do NOT call any tool more than once. "
        "Return only valid JSON, no extra text."
    ),
)


def news_node(state: StockState) -> dict:
    logger.info(f"news_agent: Running for {state['symbol']}")

    try:
        result = agent.invoke(
            {
            "messages": [
                {"role": "user", "content": f"Analyze news sentiment for {state['symbol']}. Call the tool once and return JSON."}
            ]
            },
            config={"recursion_limit":4}
        )

        last_message = result["messages"][-1].content

        if isinstance(last_message, str):
            try:
                parsed = json.loads(last_message)
                logger.info(f"news_agent: Completed for {state['symbol']}")
                return {"news": parsed}
            except Exception:
                pass

        # Fallback: find tool message for headlines, build response
        for message in result["messages"]:
            if hasattr(message, "name") and message.name == "get_news_headlines":
                try:
                    tool_result = json.loads(message.content)
                    headlines = tool_result.get("headlines", [])
                    logger.info(f"news_agent: Completed via tool message for {state['symbol']}")
                    return {"news": {
                        "headlines": headlines,
                        "analysis": last_message if isinstance(last_message, str) else "Sentiment analysis unavailable."
                    }}
                except Exception:
                    pass

        logger.info(f"news_agent: Completed with fallback for {state['symbol']}")
        return {"news": {
            "headlines": [],
            "analysis": str(last_message) if last_message else "News analysis unavailable."
        }}

    except Exception as e:
        logger.error(f"news_agent: Crashed for {state['symbol']} - {e}")
        return {"news": {"headlines": [], "analysis": "News analysis unavailable"}}