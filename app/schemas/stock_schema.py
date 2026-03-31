from dataclasses import dataclass, field
from pydantic import BaseModel
from typing import Dict, Any, Optional


@dataclass
class StockAnalysisContext:
    symbol: str
    technical: dict = field(default_factory=dict)
    news: dict = field(default_factory=dict)
    fundamental: dict = field(default_factory=dict)
    summary: str = ""


class StockRequest(BaseModel):
    symbol: str

class StockResponse(BaseModel):
    symbol: str
    resolved_symbol: Optional[str] = None
    current_price: Optional[float] = None
    technical: Dict[str, Any]
    news: Dict[str, Any]
    fundamental: Dict[str, Any]
    summary: str