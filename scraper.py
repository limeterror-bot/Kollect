import os
import json
import asyncio
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- 1. CONFIGURATION (Hiding keys using os.environ) ---
# These names must match the names you give your GitHub Secrets exactly.
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STR = os.environ.get("SESSION_STR")
TARGET_CHAT = 'me'  # You can change 'me' to a group ID if needed
BASE_URL = "https://kollectibles.in"
MONITOR_URL = f"{BASE_URL}/collections/mini-gt-india/products.json?limit=250"

async def main():
    # --- 2. CONNECT TO TELEGRAM ---
    # We use StringSession so we don't need a .session file on the server
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()

    # --- 3. LOAD LAST INVENTORY ---
    # This file is saved back to your GitHub repo after every run
    try:
        with open("inventory.json", "r") as f:
            last_inventory = json.load(f)
    except FileNotFoundError:
        last_inventory = {}

    # --- 4. SCRAPE CURRENT DATA ---
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(MONITOR_URL, headers=headers, timeout=15)
        response.raise_for_status()
       products = response.json().get('products', [])[:10]
    except Exception as e:
        print(f"❌ Scraper Error: {e}")
        return

    current_inventory = {
        str(p['id']): {
            'title': p['title'], 
            'available': any(v['available'] for v in p['variants']),
            'handle': p['handle']
        } for p in products
    }

    # --- 5. COMPARE AND NOTIFY ---
    for p_id, data in current_inventory.items():
        is_new = p_id not in last_inventory
        was_out = not last_inventory.get(p_id, {}).get('available', False)
        
        # Alert if the item is newly added OR it was out of stock and now it's back
        if data['available'] and (is_new or was_out):
            label = "✨ NEW DROP" if is_new else "🔄 RESTOCK"
            msg = f"{label}\n\n{data['title']}\n🔗 {BASE_URL}/products/{data['handle']}"
            await client.send_message(TARGET_CHAT, msg)
            print(f"📩 Alert sent for: {data['title']}")

    # --- 6. SAVE STATE FOR NEXT RUN ---
    with open("inventory.json", "w") as f:
        json.dump(current_inventory, f, indent=4)

if __name__ == "__main__":
    asyncio.run(main())
