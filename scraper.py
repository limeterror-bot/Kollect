import os
import json
import asyncio
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

# Config
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STR = os.environ.get("SESSION_STR", "")
TARGET_CHAT = 'me'
BASE_URL = "https://kollectibles.in"
MONITOR_URL = f"{BASE_URL}/collections/mini-gt-india/products.json?limit=250"

async def main():
    print("🚀 Script Started...")
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    print("✅ Connected to Telegram.")

    # Load Inventory
    try:
        with open("inventory.json", "r") as f:
            last_inventory = json.load(f)
        print(f"📦 Loaded {len(last_inventory)} items from previous run.")
    except FileNotFoundError:
        last_inventory = {}
        print("🆕 No previous inventory found. Starting fresh.")

    # Scrape Website
    print(f"🌐 Fetching data from: {MONITOR_URL}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(MONITOR_URL, headers=headers, timeout=15)
        print(f"📊 Website Response Code: {response.status_code}")
        products = response.json().get('products', [])[:10]
        print(f"🔎 Found {len(products)} products in the top 10 list.")
    except Exception as e:
        print(f"❌ Scraper Error: {e}")
        return

    current_inventory = {}
    for p in products:
        p_id = str(p['id'])
        price = p['variants'][0]['price'] if p['variants'] else "N/A"
        available = any(v['available'] for v in p['variants'])
        
        current_inventory[p_id] = {
            'title': p['title'], 
            'available': available,
            'handle': p['handle'],
            'price': price
        }
        # This will show you exactly what it's seeing for each car
        print(f"--- [ID: {p_id}] {p['title']} | Stock: {available} | Price: ₹{price}")

    # Logic check
    new_alerts = 0
    for p_id, data in current_inventory.items():
        is_new = p_id not in last_inventory
        was_out = not last_inventory.get(p_id, {}).get('available', False)
        
        if data['available'] and (is_new or was_out):
            label = "✨ NEW DROP" if is_new else "🔄 RESTOCK"
            msg = f"{label}\n\n🚗 {data['title']}\n💰 Price: ₹{data['price']}\n🔗 {BASE_URL}/products/{data['handle']}"
            await client.send_message(TARGET_CHAT, msg)
            print(f"📩 ALERT SENT: {data['title']}")
            new_alerts += 1

    if new_alerts == 0:
        print("😴 No new drops or restocks found this time.")

    with open("inventory.json", "w") as f:
        json.dump(current_inventory, f, indent=4)
    print("💾 Inventory saved. Task complete.")

if __name__ == "__main__":
    asyncio.run(main())
