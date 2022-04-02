#!python

import os
import logging

from telethon import TelegramClient, events
from collections import deque
from utils import debounce_async

TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID") or 0)
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH") or ""


def get_message_process(message):
    return deque([
        "/langen",
        "📤 Mailing",
        message,
        '✅ Send',
        "/langar"
    ])


async def send_to_bot(message, bot_username):
    # we need this global `error_occured` because we are running
    # different threads and async  code if an error occured,  we
    # should stop the next process step
    error_occured = False
    process = get_message_process(message)

    def get_message():
        """ get the next process step, return None if an error occured occured
        we ran out of the step and all are done """

        message = process.popleft()
        if len(process) == 0:
            logging.info("Alhamdulilah, all are done 💚")
        return message

    async def click_inline_button(button_name: str, event: events.NewMessage.Event | None):
        global error_occured
        if not event:
            logging.error("an event is required to click an inline button")
            error_occured = True
            return

        buttons = await event.get_buttons()

        if not buttons:
            for buttons_row in buttons:
                for button in buttons_row:
                    if button_name == button.button.text:
                        logging.info("clicking: " + button.button.text)
                        await button.click()
                        return

        all_buttons = ", ".join(
            [", ".join([button.button.text for button in buttons_row])
             for buttons_row in buttons] if buttons else [])
        logging.warning("can't find the button to click, " + button_name)
        # all the buttons chained
        logging.warning("here are the buttons: " + all_buttons)
        logging.warning("waiting for the next message")
        process.appendleft({'type': 'click-button', 'name': button_name})
        error_occured = True

    @debounce_async(0.5)
    async def send_message(event: events.NewMessage.Event | None = None):
        message = get_message()
        if type(message) is str:
            logging.info("sending: " + message)
            # type: ignore
            await telegram_client.send_message(bot_username, message)
        elif type(message) is dict:
            if message["type"] == "file":
                file_path: str = message["path"]
                logging.info("sending file: " + file_path)
                # await telegram_client.send_file(bot_username, file_path) # type: ignore
                logging.warning("ignore sending the file")
            elif message["type"] == "click-button":
                button_name = message["name"]
                await click_inline_button(button_name, event)

    async with TelegramClient('telethon', TELEGRAM_API_ID, TELEGRAM_API_HASH) as telegram_client:
        @telegram_client.on(events.NewMessage(from_users=bot_username))
        async def on_message_recieved(event):
            recieved_message = event.message.message.split("\n")[
                0]  # first line only
            logging.info("recieved: " + recieved_message)
            if error_occured or len(process) == 0 or recieved_message[0] == "❌":
                disconn_coro = telegram_client.disconnect()
                if disconn_coro:
                    await disconn_coro
            else:
                await send_message(event)

        await send_message()
        await telegram_client.run_until_disconnected()
