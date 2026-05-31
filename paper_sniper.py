import requests
import json
import time
import os
from datetime import datetime

PORTFOLIO_FILE = "paper_portfolio.json"
DAILY_LIMIT = 100
INVESTMENT_PER_COIN = 100 # USD

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    return {"date": "", "tokens": {}, "total_selected_today": 0}

def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=4)

def get_current_prices(token_addresses):
    if not token_addresses:
        return {}
    
    # DexScreener allows fetching multiple pairs
    results = {}
    # Fetch in batches of 30
    for i in range(0, len(token_addresses), 30):
        batch = token_addresses[i:i+30]
        addresses_str = ",".join(batch)
        url = f"https://api.dexscreener.com/latest/dex/tokens/{addresses_str}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                pairs = response.json().get('pairs', [])
                for p in pairs:
                    if 'priceUsd' in p and 'baseToken' in p:
                        results[p['baseToken']['address']] = float(p['priceUsd'])
        except Exception as e:
            print(f"Error updating prices: {e}", flush=True)
    return results

def get_trending_candidates():
    print("🔍 Scanning for new candidates...", flush=True)
    candidates = []
    # Search for multiple chains/terms to get more coins
    queries = [
        "solana", "meme", "pump", "moon", "pepe", "doge", "shib", "wif", "base", "ai", 
        "elon", "trump", "bonk", "grok", "bome", "slerf", "degen", "blast", "zksync", 
        "airdrop", "presale", "fairlaunch", "gem", "alpha", "whale"
    ]
    for q in queries:
        try:
            response = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={q}", timeout=10)
            if response.status_code == 200:
                candidates.extend(response.json().get('pairs', []))
        except Exception as e:
            print(f"Error fetching candidates for {q}: {e}", flush=True)
    return candidates

def filter_candidates(pairs, existing_addresses):
    candidates = []
    print(f"DEBUG: Found {len(pairs)} raw pairs from DexScreener", flush=True)
    for p in pairs:
        addr = p.get('baseToken', {}).get('address')
        if not addr or addr in existing_addresses:
            continue
            
        liquidity = float(p.get('liquidity', {}).get('usd', 0))
        volume_1h = float(p.get('volume', {}).get('h1', 0))
        
        # Relaxed criteria to ensure we can hit 100 coins
        if liquidity > 1000 and volume_1h > 1000:
            candidates.append({
                "address": addr,
                "symbol": p['baseToken']['symbol'],
                "entry_price": float(p['priceUsd']),
                "entry_time": time.time()
            })
    
    # Remove duplicates from multiple queries
    unique_candidates = []
    seen = set()
    for c in candidates:
        if c['address'] not in seen:
            unique_candidates.append(c)
            seen.add(c['address'])
            
    print(f"DEBUG: {len(unique_candidates)} unique candidates passed the filter.", flush=True)
    return unique_candidates

def update_pnl(portfolio):
    addresses = list(portfolio['tokens'].keys())
    current_prices = get_current_prices(addresses)
    
    total_pnl = 0
    for addr, data in portfolio['tokens'].items():
        if addr in current_prices:
            current_price = current_prices[addr]
            pnl_pct = ((current_price - data['entry_price']) / data['entry_price']) * 100
            data['current_price'] = current_price
            data['pnl_pct'] = pnl_pct
            total_pnl += (INVESTMENT_PER_COIN * (pnl_pct / 100))
    
    return total_pnl

def main():
    print("🚀 Paper Trading Sniper Started (100 coins/day limit)", flush=True)
    
    while True:
        portfolio = load_portfolio()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Reset limit if new day
        if portfolio.get("date") != today:
            print(f"📅 New Day: {today}. Resetting daily selection.", flush=True)
            portfolio = {"date": today, "tokens": {}, "total_selected_today": 0}

        # 1. Update existing positions
        total_pnl = update_pnl(portfolio)
        
        # 2. Select new coins if limit not reached
        selection_made = False
        if portfolio.get("total_selected_today", 0) < DAILY_LIMIT:
            pairs = get_trending_candidates()
            new_candidates = filter_candidates(pairs, portfolio['tokens'].keys())
            
            remaining = DAILY_LIMIT - portfolio["total_selected_today"]
            to_add = new_candidates[:remaining]
            
            for c in to_add:
                portfolio['tokens'][c['address']] = {
                    "symbol": c['symbol'],
                    "entry_price": c['entry_price'],
                    "entry_time": c['entry_time'],
                    "current_price": c['entry_price'],
                    "pnl_pct": 0.0
                }
            
            if to_add:
                portfolio["total_selected_today"] += len(to_add)
                selection_made = True
                print(f"➕ Added {len(to_add)} new coins. Total today: {portfolio['total_selected_today']}", flush=True)

        # 3. Report
        save_portfolio(portfolio)
        print(f"\n📈 --- Paper Trading Report ({today}) ---", flush=True)
        print(f"Total Coins Tracked: {len(portfolio['tokens'])}", flush=True)
        print(f"Cumulative PnL: ${total_pnl:,.2f}", flush=True)
        
        # Show top 5 performers
        sorted_tokens = sorted(portfolio['tokens'].values(), key=lambda x: x['pnl_pct'], reverse=True)
        print("\nTop Performers:", flush=True)
        for t in sorted_tokens[:5]:
            print(f"- ${t['symbol']}: {t['pnl_pct']:.2f}%", flush=True)
            
        # If we haven't reached our limit, wait only 1 minute before scanning again
        if portfolio["total_selected_today"] < DAILY_LIMIT:
            print(f"\n⏳ Limit ({portfolio['total_selected_today']}/{DAILY_LIMIT}) not reached. Scanning again in 1 minute...", flush=True)
            time.sleep(60)
        else:
            print("\n⏳ Daily limit reached. Waiting 1 hour for next PnL update...", flush=True)
            time.sleep(3600)

if __name__ == "__main__":
    main()
