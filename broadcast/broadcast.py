import os
import enum
import asyncio
import logging
import threading

from itertools import chain
from datetime import datetime
from collections import deque
from dateutil.relativedelta import relativedelta
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from django.conf import settings as django_settings
from django.utils.translation import gettext_lazy as _

debouncing_time = 0.5  # half a second
TELETHON_SESSION = os.environ.get("TELETHON_SESSION") or ""
TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID") or 0)
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH") or ""

broadcasting_thread = None
_is_broadcasting = False


def get_broadcating_process(message, *, image, bot_username=None):
    message_process = message
    if image:
        message_process = {
            'type': 'file',
            'file': image,
            'caption': message}

    if django_settings.IS_LOCALHOST:
        process = deque([
            "/langen",
            "📤 Mailing",
            message_process,
            "🚫 Cancel",
        ])
    else:
        process = deque([
            "/langen",
            "📤 Mailing",
            message_process,
            "✅ Send",
        ])
        if bot_username == "@Da7ee7_Civil_1st_Year_Bot":
            process.append("/langar")

    return process


def is_broadcasting():
    return _is_broadcasting


def cancel_broadcasting():
    broadcasting_thread.kill()  # type: ignore
    broadcasting_thread.join()  # type: ignore


def get_telegram_client():
    return TelegramClient(StringSession(TELETHON_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH)


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
        await asyncio.wait(tasks, timeout=30)


def send_to_bots_sync(message, *, image, bots_usernames):
    global _is_broadcasting
    _is_broadcasting = True
    logging.info("*."*10 + " sending to bots is starting")
    logging.info("-_"*20)
    logging.info(message)
    logging.info("-_"*20)
    for bot_username in bots_usernames:
        logging.info("sending to: " + bot_username)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_to_bots(
            message, image=image, bots_usernames=bots_usernames))
        loop.close()
    finally:
        logging.info("*."*10 + " sending to bots is done")
        _is_broadcasting = False


def send_to_bots_in_background(message, *, image, bots_usernames):
    # source: https://stackoverflow.com/a/21945663/10891757
    global broadcasting_thread
    # a layer of safty here
    if is_broadcasting():
        raise Exception(
            _("Can't broadcast new message while another broadcasting is running"))
    broadcasting_thread = threading.Thread(
        target=send_to_bots_sync,
        args=(message,),
        kwargs={
            'image': image,
            'bots_usernames': bots_usernames,
        })
    broadcasting_thread.daemon = True
    broadcasting_thread.start()


class MODES(enum.Enum):
    broadcasting = "broadcasting"
    settling_error = "settling_error"


async def send_to_bot(message, *, image, bot_username, telegram_client):
    # we need this global `error_occured` because we are running
    # different threads and async  code if an error occured,  we
    # should stop the next process step

    mode = MODES.broadcasting
    error_occured = False
    done = False
    process = get_broadcating_process(
        message, image=image, bot_username=bot_username)
    recieved_messages_history = []

    def get_message():
        """ get the next process step, return None if an error occured occured
        we ran out of the step and all are done """

        message = process.popleft()
        if len(process) == 0:
            logging.info(f"[{bot_username}] Alhamdulilah, all are done 💚")
        return message

    async def click_inline_button(button_name: str, event: events.NewMessage.Event | None):
        nonlocal error_occured
        if not event:
            logging.error(
                f"[{bot_username}] an event is required to click an inline button")
            error_occured = True
            return

        buttons = await event.get_buttons()

        if not buttons:
            logging.error(f"[{bot_username}] can't find any button to click")
            error_occured = True
            return

        # chain here to use one `for` loop rather than two
        for button in chain.from_iterable(buttons):
            if button_name == button.button.text:
                logging.info(bot_username + "clicking: " + button.button.text)
                return await button.click()

        all_buttons = ", ".join(
            [", ".join([button.button.text for button in buttons_row])
             for buttons_row in buttons] if buttons else [])
        logging.error(
            f"[{bot_username}] can't find the button to click, " + button_name)
        logging.error(
            f"[{bot_username}] here are the buttons: " + all_buttons)
        error_occured = True

    async def send_message(event: events.NewMessage.Event | None = None):
        nonlocal done
        message = get_message()
        if type(message) is str:
            message_first_line = message.strip().split("\n")[0]
            logging.info(f"[{bot_username}] sending: " + message_first_line)
            return await telegram_client.send_message(bot_username, message)
        if type(message) is not dict:
            raise Exception("unexpected type of message")
        if message["type"] == "file":
            logging.info(f"[{bot_username}] file sending: " + message['file'])
            return await telegram_client.send_file(bot_username, file=message['file'], caption=message['caption'])
        elif message["type"] == "click-button":
            button_name = message["name"]
            return await click_inline_button(button_name, event)

    @telegram_client.on(events.NewMessage(from_users=bot_username))
    async def _(event):
        nonlocal done, mode
        limit_of_active_mailing = "⚠️ You have reached the limit of active mailings."
        recieved_message = event.message.message.split("\n")[
            0]  # first line only
        logging.info(f"[{bot_username}] recieved: " + recieved_message)
        recieved_messages_history.append((datetime.now(), event))

        if error_occured or recieved_message[0] == "❌" or recieved_message == limit_of_active_mailing:
            if not mode == MODES.broadcasting:
                return
            # this is a solution that reconcile and settle the issue
            # and is specified for the broadcasting process to for all cases
            process.clear()
            process.append("🔙 Back")
            process.append("🚫 Cancel")
            mode = MODES.settling_error

        if len(process) == 0:
            done = True

    await send_message()
    while not done:
        if recieved_messages_history:
            last_recieved = recieved_messages_history[-1]
            debouncing_relative_datetime = relativedelta(seconds=int(debouncing_time),
                                                         microseconds=int((debouncing_time % 1) * 1e6))
            if datetime.now() > last_recieved[0] + debouncing_relative_datetime:
                recieved_messages_history = []
                await send_message(last_recieved[1])
        await asyncio.sleep(debouncing_time)
