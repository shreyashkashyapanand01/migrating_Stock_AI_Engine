def score_opportunity(stock_result):

    technical = stock_result["technical"]
    fundamental = stock_result["fundamental"]
    news = stock_result["news"]

    score = 0

    # Trend weight = 3
    if technical["trend"] == "bullish":
        score += 3

    # Momentum weight = 2
    if technical["momentum"] == "strong":
        score += 2

    # RSI weight = 2
    if technical["rsi"] == "oversold":
        score += 2

    # Valuation weight = 2
    if fundamental["valuation"] == "undervalued":
        score += 2

    # Growth weight = 1
    if fundamental["growth"] == "strong growth":
        score += 1

    if "positive" in news["analysis"].lower():
        score += 1
        
    return score