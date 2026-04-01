from pydantic import BaseModel
from typing import List


class Opportunity(BaseModel):
    symbol: str
    sector: str
    score: float
    momentum: float
    summary: str


class ScanResponse(BaseModel):
    opportunities: List[Opportunity]