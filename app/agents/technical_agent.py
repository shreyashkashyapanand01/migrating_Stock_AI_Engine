import logging
import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.tools.stock_tools import get_technical_indicators
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
    tools=[get_technical_indicators],
    prompt=(
        "You are a technical analysis specialist. "
        "Call get_technical_indicators ONCE with the stock symbol. "
        "After receiving the tool result, immediately return it as-is. "
        "Do NOT call any tool more than once. "
        "Do NOT add commentary or explanation."
    ),
)


def technical_node(state: StockState) -> dict:
    logger.info(f"technical_agent: Running for {state['symbol']}")

    try:
        result = agent.invoke(
            {
            "messages": [
                {"role": "user", "content": f"Get technical indicators for {state['symbol']}. Call the tool once and return the result."}
            ]
            },
            config={"recursion_limit":4}
        )

        # Walk messages in reverse to find the last tool result
        for message in reversed(result["messages"]):
            if hasattr(message, "content") and message.content:
                content = message.content
                if isinstance(content, str):
                    try:
                        parsed = json.loads(content)
                        if "trend" in parsed:
                            logger.info(f"technical_agent: Completed for {state['symbol']}")
                            return {"technical": parsed}
                    except Exception:
                        pass
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            try:
                                parsed = json.loads(block.get("content", "{}"))
                                if "trend" in parsed:
                                    logger.info(f"technical_agent: Completed for {state['symbol']}")
                                    return {"technical": parsed}
                            except Exception:
                                pass

        # Fallback: grab tool message directly
        for message in result["messages"]:
            if hasattr(message, "name") and message.name == "get_technical_indicators":
                try:
                    parsed = json.loads(message.content)
                    logger.info(f"technical_agent: Completed via tool message for {state['symbol']}")
                    return {"technical": parsed}
                except Exception:
                    pass

        logger.error(f"technical_agent: Could not extract result for {state['symbol']}")
        return {"technical": {}, "error": "Could not extract technical result"}

    except Exception as e:
        logger.error(f"technical_agent: Crashed for {state['symbol']} - {e}")
        return {"technical": {}, "error": "Technical agent failure"}