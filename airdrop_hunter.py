import asyncio
import os
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# List of high-signal public Telegram channels to scrape
TG_CHANNELS = [
    "AirdropAlert",
    "Airdrop6",
    "AirdropInspector",
    "CryptoAirdrops",
    "AirdropDet",
    "AirdropFinder",
    "AirdropAdventure",
    "ICO_Airdrop_Alert",
    "DeFi_Airdrops",
    "Solana_Airdrop",
    "AirdropStar",
    "Airdrop_Ninjua",
    "GemsAirdrop",
    "Airdrop_Expert",
    "Alpha_Airdrops"
]

KEYWORDS = ['airdrop', 'mint', 'claim', 'live', 'whitelist', 'presale', 'ido', 'launchpad']

async def scan_x(context):
    print(f"🔍 Scanning X...", flush=True)
    auth_token = os.getenv("X_AUTH_TOKEN")
    ct0 = os.getenv("X_CT0")
    
    if not all([auth_token, ct0]):
        print("⚠️ X session cookies missing. Skipping X scan.", flush=True)
        return

    try:
        page = await context.new_page()
        search_query = "airdrop OR mint OR presale crypto"
        url = f"https://x.com/search?q={search_query.replace(' ', '%20')}&src=typed_query&f=live"
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        tweets = await page.query_selector_all('article div[data-testid="tweetText"]')
        found_count = 0
        for tweet in tweets:
            text = await tweet.inner_text()
            if any(k in text.lower() for k in KEYWORDS):
                clean_text = text[:100].replace('\n', ' ')
                print(f"✨ Found X Airdrop/Alpha: {clean_text}...", flush=True)
                found_count += 1
        print(f"📊 X Scan found {found_count} signals.", flush=True)
        await page.close()
    except Exception as e:
        print(f"❌ X Error: {e}", flush=True)

async def scan_telegram(context):
    print("📱 Scanning Public Telegram Channels...", flush=True)
    for channel in TG_CHANNELS:
        try:
            page = await context.new_page()
            url = f"https://t.me/s/{channel}"
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            messages = await page.query_selector_all('.tgme_widget_message_text')
            for msg in messages[-5:]:
                text = await msg.inner_text()
                if any(k in text.lower() for k in KEYWORDS):
                    clean_text = text[:100].replace('\n', ' ')
                    print(f"📱 Found TG Airdrop (@{channel}): {clean_text}...", flush=True)
            await page.close()
            await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ TG Error (@{channel}): {e}", flush=True)

async def main():
    print("🚀 Airdrop Hunter Started (Free Mode - Resilient Version)...", flush=True)
    
    while True:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                
                auth_token = os.getenv("X_AUTH_TOKEN")
                ct0 = os.getenv("X_CT0")
                if auth_token and ct0:
                    await context.add_cookies([
                        {'name': 'auth_token', 'value': auth_token, 'domain': '.x.com', 'path': '/'},
                        {'name': 'ct0', 'value': ct0, 'domain': '.x.com', 'path': '/'}
                    ])
                
                await scan_x(context)
                await scan_telegram(context)
                
                await browser.close()
                print("⏳ Scan cycle complete. Waiting 10 minutes...", flush=True)
                await asyncio.sleep(600)
        except Exception as e:
            print(f"❌ Global Hunter Error: {e}. Restarting browser in 60s...", flush=True)
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
