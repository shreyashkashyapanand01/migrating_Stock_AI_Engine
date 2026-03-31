from typing import TypedDict, Optional

class StockState(TypedDict):
    symbol: str
    resolved_symbol: Optional[str]
    current_price: Optional[float]
    technical: Optional[dict]
    news: Optional[dict]
    fundamental: Optional[dict]
    summary: Optional[str]
    error: Optional[str]