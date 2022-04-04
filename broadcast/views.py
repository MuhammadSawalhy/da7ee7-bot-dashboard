from rich import inspect
import os
import re
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
from broadcast.broadcast import send_to_bots


is_broadcasting = False


def send_to_request_bots(message, image, bots_usernames=[]):
    global is_broadcasting
    is_broadcasting = True
    print("*."*10, "sending to bots is starting")
    print("-_"*20)
    print(message)
    print("-_"*20)
    bots_usernames = [bot.username for bot in Bot.objects.all()]
    for bot_username in bots_usernames:
        print("sending to", bot_username)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_to_bots(
            message, image=image, bots_usernames=bots_usernames))
        loop.close()
    finally:
        is_broadcasting = False
        print("*."*10, "sending to bots is done")


@login_required
def broadcast_page(request):
    if request.method == "GET":
        # TODO: message indicating that a broacasting is running, and a way to cancel it
        return render(request,
                      "broadcast/index.html",
                      context={
                          "bots": Bot.objects.all(),
                          "is_broadcasting": is_broadcasting
                      })

    return HttpResponse(_("Method not allowed"), status=405)


@csrf_exempt
def broadcast(request):
    if request.method == "POST":
        password = request.POST.get("password")
        bots_usernames = request.POST.get("bots")
        message = request.POST.get("message")
        image = request.FILES.get("image") or None
        if image:
            image_file_name = "telegram-image-to-send.png"
            image_path = settings.BASE_DIR / "staticfiles" / image_file_name
            with open(image_path, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
            image = f"{os.environ.get('SITE_URL')}/static/{image_file_name}"
        else:
            # an external link for an image, telethon will tell
            # telegram to fetch and send it itself
            image = request.POST.get("image_url")
            if image and not re.search(r"https://i\.suar\.me/.+", image):
                messages.error(request, _(
                    'image source should be png image from https://suar.me/'))
                return redirect('broadcast')

        inspect(image)
        if (not request.user or not request.user.is_staff) \
                and password != os.environ.get("BROADCASTING_PASSWORD"):
            return HttpResponse(_("You are not authorized to do this action"), status=401)
        if not message and not isinstance(message, str):
            return HttpResponse(_("You should specify a message"), status=400)

        if not is_broadcasting:
            # source: https://stackoverflow.com/a/21945663/10891757
            thread = threading.Thread(
                target=send_to_request_bots,
                args=(message,),
                kwargs={
                    'image': image,
                    'bots_usernames': bots_usernames,
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
