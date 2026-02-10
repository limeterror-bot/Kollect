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

# The updated URL with your specific filters applied to the JSON data
BASE_URL = "https://kollectibles.in"
MONITOR_URL = f"{BASE_URL}/collections/mini-gt-india/products.json?filter.v.availability=1&sort_by=created-descending"

async def main():
    print("🚀 Initializing Monitor with Filters...")
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    
    await client.connect()
    if not await client.is_user_authorized():
        print("❌ Auth Failed")
        return

    # Load Memory
    try:
        with open("inventory.json", "r") as f:
            last_inventory = json.load(f)
    except FileNotFoundError:
        last_inventory = {}

    # Scrape with Headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # We request the filtered JSON
        response = requests.get(MONITOR_URL, headers=headers, timeout=15)
        response.raise_for_status()
        
        # We take the top 10. Since the URL has sort_by=created-descending, 
        # index [0] is now the newest item.
        products = response.json().get('products', [])[:10]
        print(f"🔎 Found {len(products)} filtered products.")
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

    # Compare
    # We process them in reverse order [::-1] only for the MESSAGE delivery
    # so that the newest item (index 0) is the LAST message sent to Telegram.
    for p_id, data in list(current_inventory.items())[::-1]:
        if data['available'] and p_id not in last_inventory:
            msg = (
                f"✨ **NEW ARRIVAL**\n\n"
                f"🚗 **{data['title']}**\n"
                f"💰 Price: ₹{data['price']}\n"
                f"🔗 [View Product]({BASE_URL}/products/{data['handle']})"
            )
            # parse_mode='md' allows the bold text and clickable link
            await client.send_message(TARGET_CHAT, msg, parse_mode='md')
            print(f"📩 Alert: {data['title']}")

    # Save
    with open("inventory.json", "w") as f:
        json.dump(current_inventory, f, indent=4)
    print("✅ Run Complete.")

if __name__ == "__main__":
    asyncio.run(main())
