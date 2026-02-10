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
    print("🚀 Initializing...")
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    
    await client.connect()
    if not await client.is_user_authorized():
        print("❌ Auth Failed")
        return

    # Load Inventory
    try:
        with open("inventory.json", "r") as f:
            last_inventory = json.load(f)
    except FileNotFoundError:
        last_inventory = {}

    # Scrape
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(MONITOR_URL, headers=headers, timeout=15)
        # We take the top 10, then REVERSE them so the newest stays at the bottom of the chat
        products = response.json().get('products', [])[:10][::-1]
        print(f"🔎 Found {len(products)} products (Reversed for Chat Order).")
    except Exception as e:
        print(f"❌ Scrape Error: {e}")
        products = []

    current_inventory = {}
    for p in products:
        p_id = str(p['id'])
        price = p['variants'][0]['price'] if p['variants'] else "N/A"
        current_inventory[p_id] = {
            'title': p['title'], 
            'available': any(v['available'] for v in p['variants']),
            'handle': p['handle'],
            'price': price
        }

    # Compare and Notify
    for p_id, data in current_inventory.items():
        if data['available'] and p_id not in last_inventory:
            msg = f"✨ NEW DROP\n\n🚗 {data['title']}\n💰 Price: ₹{data['price']}\n🔗 {BASE_URL}/products/{data['handle']}"
            await client.send_message(TARGET_CHAT, msg)
            print(f"📩 Sent: {data['title']}")

    # Save State
    with open("inventory.json", "w") as f:
        json.dump(current_inventory, f, indent=4)
    print("✅ Done!")

if __name__ == "__main__":
    asyncio.run(main())
