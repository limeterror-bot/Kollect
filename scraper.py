import os
import json
import asyncio
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STR = os.environ.get("SESSION_STR", "")
TARGET_CHAT = -1003773854304
# We use the EXACT link you provided
PAGE_URL = "https://kollectibles.in/collections/mini-gt-india?filter.v.availability=1&sort_by=created-descending"

async def main():
    print("🚀 Initializing Visual-Order Scraper...")
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("❌ Auth Failed")
        return

    try:
        with open("inventory.json", "r") as f:
            last_inventory = json.load(f)
    except FileNotFoundError:
        last_inventory = {}

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(PAGE_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This finds the product cards in the order they appear on screen
        cards = soup.select('.grid__item')[:10]
        
        products = []
        for card in cards:
            title_el = card.select_one('.card__heading')
            link_el = card.select_one('a.full-unstyled-link')
            price_el = card.select_one('.price-item--regular')
            
            if title_el and link_el:
                title = title_el.text.strip()
                handle = link_el['href'].split('/')[-1]
                price = price_el.text.strip() if price_el else "N/A"
                # We use the handle as the ID since we are scraping HTML
                products.append({'title': title, 'handle': handle, 'price': price})
        
        print(f"🔎 Captured {len(products)} items in webpage sequence.")
        
    except Exception as e:
        print(f"❌ Scrape Error: {e}")
        products = []

    current_inventory = {}
    for p in products:
        current_inventory[p['handle']] = p

    # Process in reverse for Telegram so the #1 item is at the bottom
    for handle, data in list(current_inventory.items())[::-1]:
        if handle not in last_inventory:
            msg = (
                f"✨ **NEW ARRIVAL**\n\n"
                f"🚗 **{data['title']}**\n"
                f"💰 Price: {data['price']}\n"
                f"🔗 [View Product](https://kollectibles.in/products/{data['handle']})"
            )
            await client.send_message(TARGET_CHAT, msg, parse_mode='md')
            print(f"📩 Alert: {data['title']}")

    with open("inventory.json", "w") as f:
        json.dump(current_inventory, f, indent=4)
    print("✅ Run Complete.")

if __name__ == "__main__":
    asyncio.run(main())
