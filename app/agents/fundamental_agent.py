import logging
import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from app.tools.stock_tools import get_fundamental_data
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
    tools=[get_fundamental_data],
    prompt=(
        "You are a fundamental analysis specialist. "
        "Call get_fundamental_data ONCE with the stock symbol. "
        "After receiving the data, classify the stock: "
        "valuation as undervalued/fairly valued/overvalued based on PE ratio, "
        "growth as strong/moderate/declining based on revenue growth. "
        "Return ONLY a JSON with: valuation, growth, profit_margin, debt_to_equity. "
        "Do NOT call any tool more than once. "
        "Return only valid JSON, no extra text."
    ),
)


def fundamental_node(state: StockState) -> dict:
    logger.info(f"fundamental_agent: Running for {state['symbol']}")

    try:
        result = agent.invoke(
            {
            "messages": [
                {"role": "user", "content": f"Analyze fundamentals for {state['symbol']}. Call the tool once and return JSON."}
            ]
            },
            config={"recursion_limit":4}
        )

        last_message = result["messages"][-1].content

        if isinstance(last_message, str):
            try:
                parsed = json.loads(last_message)
                logger.info(f"fundamental_agent: Completed for {state['symbol']}")
                return {"fundamental": parsed}
            except json.JSONDecodeError:
                log.warning(f"fundamental_agent: Received invalid JSON string for {state['symbol']}")
            except Exception as e:
                log.error(f"fundamental_agent: Unexpected error parsing result for {state['symbol']} - {e}")

        # Fallback: grab raw tool result and classify locally
        for message in result["messages"]:
            if hasattr(message, "name") and message.name == "get_fundamental_data":
                try:
                    raw = json.loads(message.content)
                    pe = raw.get("pe_ratio")
                    growth = raw.get("revenue_growth")

                    valuation = "unknown"
                    if pe:
                        if pe < 15:   valuation = "undervalued"
                        elif pe < 30: valuation = "fairly valued"
                        else:         valuation = "overvalued"

                    growth_signal = "unknown"
                    if growth:
                        if growth > 0.15:  growth_signal = "strong growth"
                        elif growth > 0:   growth_signal = "moderate growth"
                        else:              growth_signal = "declining growth"

                    logger.info(f"fundamental_agent: Completed via fallback for {state['symbol']}")
                    return {"fundamental": {
                        "valuation": valuation,
                        "growth": growth_signal,
                        "profit_margin": raw.get("profit_margin"),
                        "debt_to_equity": raw.get("debt_to_equity")
                    }}
                except Exception as e:
                    log.error(f"fundamental_agent: Fallback parsing failed for {state['symbol']} - {e}")

        logger.error(f"fundamental_agent: Could not extract result for {state['symbol']}")
        return {"fundamental": {
            "valuation": "unknown", "growth": "unknown",
            "profit_margin": None, "debt_to_equity": None
        }}

    except Exception as e:
        logger.error(f"fundamental_agent: Crashed for {state['symbol']} - {e}")
        return {"fundamental": {
            "valuation": "unknown", "growth": "unknown",
            "profit_margin": None, "debt_to_equity": None
        }}







# import logging
# import json
# from dotenv import load_dotenv
# from langchain_core.messages import SystemMessage
# from langgraph.prebuilt import create_react_agent
# from app.tools.stock_tools import get_fundamental_data
# from app.state.stock_state import StockState
# #from app.config import get_llm
# from langchain_groq import ChatGroq
# import os

# load_dotenv()
# logger = logging.getLogger(__name__)

# llm = ChatGroq(
#     model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
#     api_key=os.getenv("GROQ_API_KEY"),
#     temperature=0.3
# )

# system_msg = SystemMessage(content=(
#     "You are a fundamental analysis specialist. "
#     "Call get_fundamental_data ONCE using the EXACT symbol string the user provides — do not resolve, translate, or modify it to a ticker. "
#     "The tool handles ticker resolution internally. "
#     "After receiving the data classify: "
#     "valuation as undervalued/fairly valued/overvalued based on PE ratio, "
#     "growth as strong/moderate/declining based on revenue growth. "
#     "Return ONLY valid JSON with exactly these keys: valuation, growth, profit_margin, debt_to_equity. "
#     "Do NOT call any tool more than once. No explanation, no extra text, only JSON."
# ))

# agent = create_react_agent(
#     model=llm,
#     tools=[get_fundamental_data],
# )


# def fundamental_node(state: StockState) -> dict:
#     logger.info(f"fundamental_agent: Running for {state['symbol']}")

#     try:
#         result = agent.invoke(
#             {
#                 "messages": [
#                     system_msg,
#                     {"role": "user", "content": f"Analyze fundamentals for '{state['symbol']}'. Pass exactly '{state['symbol']}' to the tool without any modification."}
#                 ]
#             },
#             config={"recursion_limit": 2}
#         )

#         last_message = result["messages"][-1].content

#         if isinstance(last_message, str):
#             try:
#                 parsed = json.loads(last_message)
#                 logger.info(f"fundamental_agent: Completed for {state['symbol']}")
#                 return {"fundamental": parsed}
#             except Exception:
#                 pass

#         # Fallback: find tool result and classify locally
#         for message in result["messages"]:
#             if hasattr(message, "name") and message.name == "get_fundamental_data":
#                 try:
#                     raw = json.loads(message.content)
#                     pe     = raw.get("pe_ratio")
#                     growth = raw.get("revenue_growth")

#                     valuation = "unknown"
#                     if pe:
#                         if pe < 15:   valuation = "undervalued"
#                         elif pe < 30: valuation = "fairly valued"
#                         else:         valuation = "overvalued"

#                     growth_signal = "unknown"
#                     if growth:
#                         if growth > 0.15: growth_signal = "strong growth"
#                         elif growth > 0:  growth_signal = "moderate growth"
#                         else:             growth_signal = "declining growth"

#                     logger.info(f"fundamental_agent: Completed via fallback for {state['symbol']}")
#                     return {"fundamental": {
#                         "valuation":      valuation,
#                         "growth":         growth_signal,
#                         "profit_margin":  raw.get("profit_margin"),
#                         "debt_to_equity": raw.get("debt_to_equity")
#                     }}
#                 except Exception:
#                     pass

#         logger.error(f"fundamental_agent: Could not extract result for {state['symbol']}")
#         return {"fundamental": {
#             "valuation": "unknown", "growth": "unknown",
#             "profit_margin": None, "debt_to_equity": None
#         }}

#     except Exception as e:
#         logger.error(f"fundamental_agent: Crashed for {state['symbol']} - {e}")
#         return {"fundamental": {
#             "valuation": "unknown", "growth": "unknown",
#             "profit_margin": None, "debt_to_equity": None
#         }}