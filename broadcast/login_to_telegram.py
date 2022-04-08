#!python
import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID") or 0)
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH") or ""


async def login_to_telegram():
    client = TelegramClient(
        StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    async with client:
        print(f"TELETHON_SESSION={client.session.save()}")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(login_to_telegram())
