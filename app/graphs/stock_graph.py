import logging
from langgraph.graph import StateGraph, START, END
from app.state.stock_state import StockState
from app.agents.technical_agent import technical_node
from app.agents.news_agent import news_node
from app.agents.fundamental_agent import fundamental_node
from app.agents.decision_agent import decision_node
from app.tools.market_data_tool import get_stock_name, fetch_latest_price


logger = logging.getLogger(__name__)


def build_stock_graph():
    builder = StateGraph(StockState)

    builder.add_node("technical_agent",    technical_node)
    builder.add_node("news_agent",         news_node)
    builder.add_node("fundamental_agent",  fundamental_node)
    builder.add_node("decision_agent",     decision_node)

    # Fan-out: START triggers all three specialists in parallel
    builder.add_edge(START, "technical_agent")
    builder.add_edge(START, "news_agent")
    builder.add_edge(START, "fundamental_agent")

    # Fan-in: all three feed into decision
    builder.add_edge("technical_agent",   "decision_agent")
    builder.add_edge("news_agent",        "decision_agent")
    builder.add_edge("fundamental_agent", "decision_agent")

    builder.add_edge("decision_agent", END)

    #return builder.compile()
    return builder.compile(checkpointer=None)


stock_graph = build_stock_graph()


def run_stock_graph(symbol: str) -> dict:
    logger.info(f"stock_graph: Starting analysis for {symbol}")

    try:
        
        resolved = get_stock_name(symbol)
        price    = fetch_latest_price(symbol)
        
        logger.info(f"stock_graph: Resolved '{symbol}' -> '{resolved}', price: {price}")
                    
        result = stock_graph.invoke({
            "symbol":          symbol,
            "resolved_symbol": resolved,
            "current_price":   price,
            "technical":       None,
            "news":            None,
            "fundamental":     None,
            "summary":         None,
            "error":           None
        })

        if result.get("error"):
            logger.error(f"stock_graph: Completed with error for {symbol}")
            return {"symbol": symbol, "error": result["error"]}

        logger.info(f"stock_graph: Successfully completed for {symbol}")
       
        return {
            "symbol":          symbol,
            "resolved_symbol": result.get("resolved_symbol", resolved),
            "current_price":   result.get("current_price", price),
            "technical":       result.get("technical", {}),
            "news":            result.get("news", {}),
            "fundamental":     result.get("fundamental", {}),
            "summary":         result.get("summary", "")
        }

    except Exception as e:
        logger.error(f"stock_graph: Crashed for {symbol} - {e}")
        return {"symbol": symbol, "error": "Graph execution failed"}



# import logging
# from langgraph.graph import StateGraph, START, END
# from app.state.stock_state import StockState
# from app.agents.technical_agent import technical_node
# from app.agents.news_agent import news_node
# from app.agents.fundamental_agent import fundamental_node
# from app.agents.decision_agent import decision_node
# from app.tools.market_data_tool import get_stock_name, fetch_latest_price

# logger = logging.getLogger(__name__)


# def build_stock_graph():
#     builder = StateGraph(StockState)

#     builder.add_node("technical_agent",   technical_node)
#     builder.add_node("news_agent",        news_node)
#     builder.add_node("fundamental_agent", fundamental_node)
#     builder.add_node("decision_agent",    decision_node)

#     builder.add_edge(START, "technical_agent")
#     builder.add_edge(START, "news_agent")
#     builder.add_edge(START, "fundamental_agent")

#     builder.add_edge("technical_agent",   "decision_agent")
#     builder.add_edge("news_agent",        "decision_agent")
#     builder.add_edge("fundamental_agent", "decision_agent")

#     builder.add_edge("decision_agent", END)

#     return builder.compile(checkpointer=None)


# stock_graph = build_stock_graph()


# def run_stock_graph(symbol: str) -> dict:
#     logger.info(f"stock_graph: Starting analysis for {symbol}")

#     try:
#         # Resolve ticker ONCE — pass resolved symbol into graph
#         resolved = get_stock_name(symbol)
#         price    = fetch_latest_price(resolved)  # pass resolved, not raw

#         logger.info(f"stock_graph: Resolved '{symbol}' -> '{resolved}', price: {price}")

#         result = stock_graph.invoke({
#             "symbol":          resolved,  # agents use resolved ticker directly
#             "resolved_symbol": resolved,
#             "current_price":   price,
#             "technical":       None,
#             "news":            None,
#             "fundamental":     None,
#             "summary":         None,
#             "error":           None
#         })

#         if result.get("error"):
#             logger.error(f"stock_graph: Completed with error for {symbol}")
#             return {"symbol": symbol, "error": result["error"]}

#         logger.info(f"stock_graph: Successfully completed for {symbol}")
#         return {
#             "symbol":          symbol,
#             "resolved_symbol": resolved,
#             "current_price":   price,
#             "technical":       result.get("technical", {}),
#             "news":            result.get("news", {}),
#             "fundamental":     result.get("fundamental", {}),
#             "summary":         result.get("summary", "")
#         }

#     except Exception as e:
#         logger.error(f"stock_graph: Crashed for {symbol} - {e}")
#         return {"symbol": symbol, "error": "Graph execution failed"}