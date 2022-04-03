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
        process = deque([message_process])
    else:
        process = deque([
            "/langen",
            "📤 Mailing",
            message_process,
            '✅ Send',
            "/langar",
        ])

    return process


async def send_to_bot(message, *, image, bot_username):
    # we need this global `error_occured` because we are running
    # different threads and async  code if an error occured,  we
    # should stop the next process step
    error_occured = False
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
        logging.warning(f"[{bot_username}] here are the buttons: " + all_buttons)
        logging.warning(f"[{bot_username}] waiting for the next message")
        process.appendleft({'type': 'click-button', 'name': button_name})
        error_occured = True

    @debounce_async(0.5)
    async def send_message(event: events.NewMessage.Event | None = None):
        message = get_message()
        if type(message) is str:
            logging.info(f"[{bot_username}] sending: " + message)
            # type: ignore
            await telegram_client.send_message(bot_username, message)
        elif type(message) is dict:
            if message["type"] == "file":
                logging.info(f"[{bot_username}] sending file")
                await telegram_client.send_file(bot_username, file=message['file'], caption=message['caption'])
            elif message["type"] == "click-button":
                button_name = message["name"]
                await click_inline_button(button_name, event)

    async with TelegramClient(f'telethon.{TELETHON_SESSION}', TELEGRAM_API_ID, TELEGRAM_API_HASH) as telegram_client:
        @telegram_client.on(events.NewMessage(from_users=bot_username))
        async def on_message_recieved(event):
            recieved_message = event.message.message.split("\n")[
                0]  # first line only
            logging.info(f"[{bot_username}] recieved: " + recieved_message)
            if error_occured or len(process) == 0 or recieved_message[0] == "❌":
                disconn_coro = telegram_client.disconnect()
                if disconn_coro:
                    await disconn_coro
            else:
                await send_message(event)

        await send_message()
        await telegram_client.run_until_disconnected()
