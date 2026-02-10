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

# 🛠️ UPDATE THIS: Use your Channel ID (e.g., -100...) or @username
TARGET_CHAT = -100123456789 

# 🛠️ UPDATE THIS: Your actual Telegram @username to force a notification ping
MY_HANDLE = "@lemonsnickers" 

PAGE_URL = "https://kollectibles.in/collections/mini-gt-india?filter.v.availability=1&sort_by=created-descending"

async def main():
    print("🚀 Running Pro Scraper with Audio-Force Hack...")
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("❌ Auth Failed - Check your SESSION_STR")
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
            
            # Extract Image URL cleanly
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

    current_inventory = {p['handle']: p for p in
