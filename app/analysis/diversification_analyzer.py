import logging
from app.analysis.sector_mapper import get_sector

logger = logging.getLogger(__name__)


def analyze_diversification(holdings):
    logger.info("diversification_analyzer: Started analyzing portfolio diversification")

    try:
        sector_allocation = {}

        for h in holdings:
            sector = get_sector(h.symbol)
            sector_allocation[sector] = sector_allocation.get(sector, 0) + h.quantity

        if not sector_allocation:
            logger.warning("diversification_analyzer: No holdings to analyze")
            return {"sectorExposure": {}, "risk": "No holdings"}

        total = sum(sector_allocation.values())

        sector_percent = {
            k: round((v / total) * 100, 2) for k, v in sector_allocation.items()
        }

        max_sector = max(sector_percent, key=sector_percent.get)

        risk = "Well Diversified"
        if sector_percent[max_sector] > 60:
            risk = f"High concentration in {max_sector}"

        logger.info(f"diversification_analyzer: Successfully finished diversification analysis (Max Sector: {max_sector})")
        return {
            "sectorExposure": sector_percent,
            "risk": risk
        }

    except Exception as e:
        logger.error(f"Error in diversification_analyzer.py at analyze_diversification: {str(e)}")
        return {
            "sectorExposure": {},
            "risk": "Error during analysis"
        }