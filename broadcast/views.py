from rich import inspect
import os
import re
import multiprocessing
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


broadcasting_process = None


def is_broadcasting():
    return broadcasting_process and broadcasting_process.is_alive()


def send_to_request_bots(message, image, bots_usernames):
    print("*."*10, "sending to bots is starting")
    print("-_"*20)
    print(message)
    print("-_"*20)
    for bot_username in bots_usernames:
        print("sending to", bot_username)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_to_bots(
            message, image=image, bots_usernames=bots_usernames))
        loop.close()
    finally:
        print("*."*10, "sending to bots is done")
        import sys
        sys.exit()


@login_required
def broadcast_page(request):
    if request.method == "GET":
        # TODO: message indicating that a broacasting is running, and a way to cancel it
        return render(request,
                      "broadcast/index.html",
                      context={
                          "bots": Bot.objects.all(),
                          "is_broadcasting": is_broadcasting()
                      })

    return HttpResponse(_("Method not allowed"), status=405)


@csrf_exempt
def broadcast(request):
    if request.method == "POST":
        global broadcasting_process
        password = request.POST.get("password")
        bots_usernames = request.POST.get("bots")
        bots_usernames = [bot.username for bot in Bot.objects.all()]
        message = request.POST.get("message") or ""
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

        if (not request.user or not request.user.is_staff) \
                and password != os.environ.get("BROADCASTING_PASSWORD"):
            return HttpResponse(_("You are not authorized to do this action"), status=401)
        if not message and not image:
            messages.error(request, _("You should specify a message"))
            return redirect('broadcast')
        if image and len(message) > 1024:
            messages.error(request, _("Image caption should not excceed 1024 chars"))
            return redirect('broadcast')

        if not is_broadcasting():
            # source: https://stackoverflow.com/a/21945663/10891757
            broadcasting_process = multiprocessing.Process(
                target=send_to_request_bots,
                args=(message,),
                kwargs={
                    'image': image,
                    'bots_usernames': bots_usernames,
                })
            broadcasting_process.daemon = True
            broadcasting_process.start()
            messages.success(request, _(
                'message is being broadcasted, it may take some time'))
        else:
            messages.error(request, _(
                'another broadcasting is in progress, please wait!'))
        return redirect('broadcast')

    return HttpResponse(_("Method not allowed"), status=405)


@csrf_exempt
def cancel(request):
    if is_broadcasting():
        broadcasting_process.kill() # type: ignore
        broadcasting_process.join() # type: ignore
        messages.success(request, _(
            'the previous running broadcasting was successfully canceled'))
    else:
        messages.error(request, _(
            'no running broadcasting exists'))
    return redirect('broadcast')
