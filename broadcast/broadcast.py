import asyncio
import os
import logging

from telethon import TelegramClient, events
from collections import deque
from utils import debounce_async
from django.conf import settings as django_settings

TELETHON_SESSION = os.environ.get("TELETHON_SESSION") or "default"
TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID") or 0)
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH") or ""


def get_message_process(message, *, image):
    message_process = message
    if image:
        message_process = {
            'type': 'file',
            'file': image,
            'caption': message}

    if django_settings.IS_LOCALHOST:
        process = deque([message_process, ])
    else:
        process = deque([
            "/langen",
            "📤 Mailing",
            message_process,
            '✅ Send',
            "/langar",
        ])

    return process


def get_telegram_client():
    return TelegramClient(f'telethon.{TELETHON_SESSION}', TELEGRAM_API_ID, TELEGRAM_API_HASH)


async def send_to_bots(message, *, image, bots_usernames):
    async with get_telegram_client() as telegram_client:
        tasks = []
        for bot_username in bots_usernames:
            task = asyncio.create_task(
                send_to_bot(message, image=image,
                            bot_username=bot_username,
                            telegram_client=telegram_client)
            )
            tasks.append(task)
        await asyncio.wait(tasks, timeout=1.5*60)


async def send_to_bot(message, *, image, bot_username, telegram_client):
    # we need this global `error_occured` because we are running
    # different threads and async  code if an error occured,  we
    # should stop the next process step
    error_occured = False
    done = False
    process = get_message_process(message, image=image)

    def get_message():
        """ get the next process step, return None if an error occured occured
        we ran out of the step and all are done """

        message = process.popleft()
        if len(process) == 0:
            logging.info(f"[{bot_username}] Alhamdulilah, all are done 💚")
        return message

    async def click_inline_button(button_name: str, event: events.NewMessage.Event | None):
        global error_occured
        if not event:
            logging.error(
                bot_username + "an event is required to click an inline button")
            error_occured = True
            return

        buttons = await event.get_buttons()

        if not buttons:
            for buttons_row in buttons:
                for button in buttons_row:
                    if button_name == button.button.text:
                        logging.info(bot_username +
                                     "clicking: " + button.button.text)
                        await button.click()
                        return

        all_buttons = ", ".join(
            [", ".join([button.button.text for button in buttons_row])
             for buttons_row in buttons] if buttons else [])
        logging.warning(
            bot_username + "can't find the button to click, " + button_name)
        # all the buttons chained
        logging.warning(
            f"[{bot_username}] here are the buttons: " + all_buttons)
        logging.warning(f"[{bot_username}] waiting for the next message")
        process.appendleft({'type': 'click-button', 'name': button_name})
        error_occured = True

    @debounce_async(0.5)
    async def send_message(event: events.NewMessage.Event | None = None):
        nonlocal done
        message = get_message()
        if type(message) is str:
            await telegram_client.send_message(bot_username, message)
            logging.info(f"[{bot_username}] sent: " + message)
            done = True
        elif type(message) is dict:
            if message["type"] == "file":
                await telegram_client.send_file(bot_username, file=message['file'], caption=message['caption'])
                logging.info(f"[{bot_username}] file sent: " + message['file'])
            elif message["type"] == "click-button":
                button_name = message["name"]
                await click_inline_button(button_name, event)

    @telegram_client.on(events.NewMessage(from_users=bot_username))
    async def _(event):
        nonlocal done
        recieved_message = event.message.message.split("\n")[
            0]  # first line only
        logging.info(f"[{bot_username}] recieved: " + recieved_message)

        if error_occured or len(process) == 0 or recieved_message[0] == "❌":
            done = True
        else:
            await send_message(event)

    await send_message()
    while not done:
        await asyncio.sleep(1)
