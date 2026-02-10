import os
import json
import requests
from bs4 import BeautifulSoup

# --- CONFIG ---
# Get these from GitHub Secrets
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
TARGET_CHAT = -1003773854304  # Your Channel ID
MY_HANDLE = "@lemonsnickers"

PAGE_URL = "https://kollectibles.in/collections/mini-gt-india?filter.v.availability=1&sort_by=created-descending"

def send_telegram(msg, image_url=None):
    """Sends message via Bot API (Appears as the Bot, not You)"""
    if image_url:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        data = {"chat_id": TARGET_CHAT, "photo": image_url, "caption": msg, "parse_mode": "HTML"}
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": TARGET_CHAT, "text": msg, "parse_mode": "HTML"}
    
    r = requests.post(url, data=data)
    return r.json()

def main():
    print("🚀 Running Bot-Monitor...")
    
    try:
        with open("inventory.json", "r") as f:
            last_inventory = json.load(f)
    except FileNotFoundError:
        last_inventory = {}

    headers = {'User-Agent': 'Mozilla/5.0'}
    
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
            msg = f"""🚨 <b>{MY_HANDLE} NEW DROP!</b>

🚗 <b>{p['title']}</b>
💰 Price: {p['price']}
🔗 <a href='https://kollectibles.in/products/{p['handle']}'>View Product</a>"""
            
            res = send_telegram(msg, p['image'])
            if res.get("ok"):
                print(f"📩 Bot Sent: {p['title']}")
            else:
                print(f"⚠️ Bot Error: {res}")

    with open("inventory.json", "w") as f:
        json.dump(current_inventory, f, indent=4)
    print("✅ Done!")

if __name__ == "__main__":
    main()
