from rich import inspect
import os
import threading
import asyncio
from bots.models import Bot

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.files.base import File


from broadcast.broadcast import send_to_bot


is_broadcasting = False


def send_to_bots(message, image, bot_username):
    global is_broadcasting
    is_broadcasting = True
    print("*."*10, "sending to bots is starting")
    bots = Bot.objects.all()
    if bot_username:
        bots = bots.filter(username=bot_username)
    print("-_"*20)
    print(message)
    print("-_"*20)
    for bot in bots:
        print("sending to", bot.username)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for bot in bots:
            loop.run_until_complete(send_to_bot(
                message, image=image, bot_username=bot.username))
        loop.close()
    finally:
        is_broadcasting = False
        print("*."*10, "sending to bots is done")


@login_required
def broadcast_page(request):
    if request.method == "GET":
        return render(request, "broadcast/index.html", context={"bots": Bot.objects.all()})

    return HttpResponse(_("Method not allowed"), status=405)


@csrf_exempt
def broadcast(request):
    if request.method == "POST":
        password = request.POST.get("password")
        bot_username = request.POST.get("bot")
        message = request.POST.get("message")
        image = request.FILES.get("image") or None
        if image:
            image_path = settings.BASE_DIR / "broadcast" / "image-to-send.png"
            with open(image_path, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
            image = image_path
        else:
            # an external link for an image, telethon will tell
            # telegram to fetch and send it itself
            image = image or request.POST.get("image") or None

        if (not request.user or not request.user.is_staff) \
                and password != os.environ.get("BROADCASTING_PASSWORD"):
            return HttpResponse(_("You are not authorized to do this action"), status=401)
        if not message and not isinstance(message, str):
            return HttpResponse(_("You should specify a message"), status=400)

        if not is_broadcasting:
            # source: https://stackoverflow.com/a/21945663/10891757
            thread = threading.Thread(
                target=send_to_bots,
                args=(message,),
                kwargs={
                    'image': image,
                    'bot_username': bot_username,
                })
            thread.daemon = True
            thread.start()
            messages.success(request, _(
                'message is being broadcasted, it may take some time'))
        else:
            messages.error(request, _(
                'another broadcasting is in progress, please wait!'))
        return redirect('broadcast')

    return HttpResponse(_("Method not allowed"), status=405)
