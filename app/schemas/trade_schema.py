from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Trade(BaseModel):
    symbol:         str
    entry_price:    float
    exit_price:     float
    quantity:       int
    entry_time:     Optional[datetime] = None
    exit_time:      Optional[datetime] = None
    type:           str
    side:           str
    holdingMinutes: float
    profitLoss:     float


class TradeAnalysisRequest(BaseModel):
    trades: List[Trade]


class TradeAnalysisResponse(BaseModel):
    analysisId:  str
    generatedAt: str
    riskScore:   int
    traderType:  str
    mistakes:    List[str]
    metrics:     dict
    summary:     str
    suggestions: List[str]
