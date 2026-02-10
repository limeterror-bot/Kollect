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

async def main():
    print("Step 1: Initializing Client...")
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    
    try:
        # This will time out after 30 seconds if it can't connect
        await asyncio.wait_for(client.connect(), timeout=30)
    except asyncio.TimeoutError:
        print("❌ ERROR: Connection Timed Out. GitHub might be blocked or Session is bad.")
        return

    print("Step 2: Checking Authorization...")
    if not await client.is_user_authorized():
        print("❌ ERROR: Your SESSION_STR is not authorized. You must re-run the local script and get a NEW string.")
        return
    
    print("✅ SUCCESS: Connected and Authorized!")
    
    # Simple test message
    await client.send_message('me', "✅ Monitor is Online!")
    print("Step 3: Test Message Sent to 'Saved Messages'.")

if __name__ == "__main__":
    try:
        # Forces the whole thing to die after 60 seconds max
        asyncio.run(asyncio.wait_for(main(), timeout=60))
    except Exception as e:
        print(f"Final Crash: {e}")
