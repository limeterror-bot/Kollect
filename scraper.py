import os
import json
import asyncio
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STR = os.environ.get("SESSION_STR", "")
TARGET_CHAT = 'me'
BASE_URL = "https://kollectibles.in"
# We pull a larger batch (50) to make sure we don't miss anything after filtering
MONITOR_URL = f"{BASE_URL}/collections/mini-gt-india/products.json?limit=50"

async def main():
    print("🚀 Initializing Smart-Sort Monitor...")
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

    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(MONITOR_URL, headers=headers, timeout=15)
        all_products = response.json().get('products', [])
        
        # 1. Filter for In-Stock only
        instock_products = [
            p for p in all_products 
            if any(v['available'] for v in p['variants'])
        ]
        
        # 2. SORT MANUALLY: Newest ID first
        # This fixes the Shopify sorting issue permanently.
        instock_products.sort(key=lambda x: x['id'], reverse=True)
        
        # 3. Take the top 10 newest
        products = instock_products[:10]
        print(f"🔎 Found {len(products)} in-stock products, sorted by Newest ID.")
        
    except Exception as e:
        print(f"❌ Scrape Error: {e}")
        products = []

    current_inventory = {}
    for p in products:
        p_id = str(p['id'])
        price = p['variants'][0]['price'] if p['variants'] else "N/A"
        current_inventory[p_id] = {
            'title': p['title'], 
            'available': True,
            'handle': p['handle'],
            'price': price
        }

    # Reverse for Telegram display (so the #1 newest is at the bottom of the chat)
    for p_id, data in list(current_inventory.items())[::-1]:
        if p_id not in last_inventory:
            msg = (
                f"✨ **NEW ARRIVAL**\n\n"
                f"🚗 **{data['title']}**\n"
                f"💰 Price: ₹{data['price']}\n"
                f"🔗 [View Product]({BASE_URL}/products/{data['handle']})"
            )
            await client.send_message(TARGET_CHAT, msg, parse_mode='md')
            print(f"📩 Alert: {data['title']}")

    with open("inventory.json", "w") as f:
        json.dump(current_inventory, f, indent=4)
    print("✅ Run Complete.")

if __name__ == "__main__":
    asyncio.run(main())
