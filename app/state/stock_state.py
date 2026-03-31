from typing import TypedDict, Optional

class StockState(TypedDict):
    symbol: str

    technical: Optional[dict]
    news: Optional[dict]
    fundamental: Optional[dict]

    summary: Optional[str]
    error: Optional[str]