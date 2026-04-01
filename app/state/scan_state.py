from typing import TypedDict, List, Optional, Any


class StockCandidate(TypedDict):
    symbol: str
    sector: str
    perChange: float
    ltp: float


class OpportunityResult(TypedDict):
    symbol: str
    sector: str
    score: float
    momentum: float
    summary: str


class ScanState(TypedDict):
    # universe_node output
    candidates:    List[StockCandidate]

    analyzed:      List[Any]       
    
    # analysis + scoring node output
    opportunities: List[OpportunityResult]

    # error
    error:         Optional[str]