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

# 🛠️ UPDATE THESE:
TARGET_CHAT = -100123456789  # Your Channel ID
MY_HANDLE = "@lemonsnickers"  # Your @username inside quotes

PAGE_URL = "https://kollectibles.in/collections/mini-gt-india?filter.v.availability=1&sort_by=created-descending"

async def main():
    print("🚀 Running Monitor with @Mention...")
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
        cards = soup.find_all('li', class_='grid__item')[:10]
        
        products = []
        for card in cards:
            title_el = card.find('h3', class_='card__heading')
            link_el = card.find('a', class_='full-unstyled-link')
            price_el = card.find('span', class_='price-item--regular')
            img_el = card.find('img')
            
            img_url = None
            if img_el:
                img_src = img_el.get('src') or img_el.get('data-src')
                if img_src:
                    img_url = "https:" + img_src if img_src.startswith('//') else img_src
            
            if title_el and link_el:
                products.append({
                    'title': title_el.get_text(strip=True),
                    'handle': link_el['href'].split('/')[-1].split('?')[0],
                    'price': price_el.get_text(strip=True) if price_el else "N/A",
                    'image': img_url
                })
    except Exception as e:
        print(f"❌ Scrape Error: {e}")
        products = []

    current_inventory = {p['handle']: p for p in products}

    for p in reversed(products):
        if p['handle'] not in last_inventory:
            # We keep the mention here in the text
            msg = (
                f"🔔 {MY_HANDLE} **NEW DROP!**\n\n"
                f"🚗 **{p['title']}**\n"
                f"💰 Price: {p['price']}\n"
                f"🔗 [View Product](https://kollectibles.in/products/{p['handle']})"
            )
            
            try:
                if p['image']:
                    # Removed 'silent=False' so it uses default Telegram behavior
                    await client.send_file(TARGET_CHAT, p['image'], caption=msg, parse_mode='md')
                else:
                    await client.send_message(TARGET_CHAT, msg, parse_mode='md')
                print(f"📩 Sent: {p['title']}")
                await asyncio.sleep(1) 
            except Exception as e:
                print(f"⚠️ Send Error: {e}")

    with open("inventory.json", "w") as f:
        json.dump(current_inventory, f, indent=4)
    print("✅ Run Complete.")

if __name__ == "__main__":
    asyncio.run(main())
