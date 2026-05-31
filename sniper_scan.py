import requests
import json
import time

def get_trending():
    # Attempting to fetch trending tokens. Note: DexScreener API specifics might vary.
    # If /trending is not available, we search for common meme terms or use specific chain endpoints.
    try:
        response = requests.get("https://api.dexscreener.com/latest/dex/search?q=solana") # Searching solana for high activity
        if response.status_code == 200:
            return response.json().get('pairs', [])
    except Exception as e:
        print(f"Error fetching DexScreener: {e}")
    return []

def get_macro():
    try:
        response = requests.get("https://api.coincap.io/v2/assets?limit=10")
        if response.status_code == 200:
            return response.json().get('data', [])
    except Exception as e:
        print(f"Error fetching CoinCap: {e}")
    return []

def filter_tokens(pairs):
    filtered = []
    now = time.time() * 1000
    for p in pairs:
        created_at = p.get('pairCreatedAt', 0)
        liquidity = float(p.get('liquidity', {}).get('usd', 0))
        volume_1h = float(p.get('volume', {}).get('h1', 0))
        price_change_1h = float(p.get('priceChange', {}).get('h1', 0))
        
        # Filtering: Created < 24h (86400000 ms), Liquidity > $50k, Volume 1h > $100k, Change 1h > 20%
        # Note: pairCreatedAt might be 0 for some old pairs or missing data, so we check carefully.
        age_ms = now - created_at
        if age_ms < 86400000 and liquidity > 50000 and volume_1h > 100000 and price_change_1h > 20:
            filtered.append(p)
    return filtered

pairs = get_trending()
filtered = filter_tokens(pairs)
macro = get_macro()

results = {
    "filtered_tokens": filtered[:5],
    "macro": macro
}
print(json.dumps(results, indent=2))
