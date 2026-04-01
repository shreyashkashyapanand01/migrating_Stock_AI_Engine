import logging
import requests

from app.config import top_limit, per_sector_limit

logger = logging.getLogger(__name__)

def fetch_top_sector_performers(limit_per_sector=per_sector_limit, total_top_limit=top_limit):
    logger.info("gainer_provider: Started fetching top sector performers from NSE")
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }

    # Step 1: Initialize session and get cookies
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
    except Exception as e:
        logger.error(f"Error in gainer_provider.py at fetch_top_sector_performers: Connection Error: {e}")
        return []

    # Step 2: Fetch the Analysis Data
    url = "https://www.nseindia.com/api/live-analysis-variations?index=gainers"
    response = session.get(url, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Error in gainer_provider.py at fetch_top_sector_performers: Error fetching data: {response.status_code}")
        return []

    data = response.json()
    all_selected_stocks = []
    seen_symbols = set()  # To avoid duplicates if a stock is in multiple indices

    # Step 3: Iterate through each sector/index in the legends
    # The 'legends' key contains the list of available index keys (e.g., 'NIFTY', 'BANKNIFTY')
    indices = [item[0] for item in data.get('legends', [])]

    for index_key in indices:
        sector_data = data.get(index_key, {}).get('data', [])
        
        # Take the top 3 from this sector
        top_3_in_sector = sector_data[:limit_per_sector]

        for stock in top_3_in_sector:
            symbol = stock.get('symbol')
            
            # Skip if we already processed this stock from a previous sector
            if symbol in seen_symbols:
                continue
            
            ltp = stock.get('ltp', 0)
            prev_price = stock.get('prev_price', 0)

            # Step 4: Calculate perChange using your formula
            # Formula: ((ltp - prev_price) / prev_price) * 100
            if prev_price != 0:
                calculated_change = ((ltp - prev_price) / prev_price) * 100
            else:
                calculated_change = 0

            all_selected_stocks.append({
                "symbol": symbol,
                "sector": index_key,
                "perChange": calculated_change,
                "ltp": ltp
            })
            seen_symbols.add(symbol)

    # Step 5: Sort all collected stocks by perChange in descending order
    sorted_stocks = sorted(all_selected_stocks, key=lambda x: x['perChange'], reverse=True)

    # Return only the top 15
    logger.info(f"gainer_provider: Successfully finished fetching {len(sorted_stocks[:total_top_limit])} stocks")
    return sorted_stocks[:total_top_limit]