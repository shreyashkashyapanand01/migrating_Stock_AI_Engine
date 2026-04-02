from typing import TypedDict, List, Optional


class TradeState(TypedDict):
    # Input
    trades:       List[dict]

    # metrics_node output
    metrics:      dict

    # pattern_node output
    mistakes:     List[str]

    # behaviour_node output
    risk_score:   int
    trader_type:  str
    summary:      str
    suggestions:  List[str]

    # error propagation
    error:        Optional[str]