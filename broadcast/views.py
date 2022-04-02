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

from broadcast.broadcast import send_to_bot


def send_to_bots(message, bot_username):
    bots = Bot.objects.all()
    if bot_username:
        bots = bots.filter(username=bot_username)
    print("-_"*20)
    print(message)
    print("-_"*20)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for bot in bots:
        print("sending to", bot.username)
        loop.run_until_complete(send_to_bot(message, bot.username))


@login_required
def broadcast_page(request):
    if request.method == "GET":
        return render(request, "broadcast/index.html", context={"bots": Bot.objects.all()})

    return HttpResponse(_("Method not allowed"), status=405)


@csrf_exempt
def broadcast(request):
    if request.method == "POST":
        password = request.POST.get("password")
        message = request.POST.get("message")
        bot_username = request.POST.get("bot")

        if (not request.user or not request.user.is_staff) \
                and password != os.environ.get("BROADCASTING_PASSWORD"):
            return HttpResponse(_("You are not authorized to do this action"), status=401)
        if not message and not isinstance(message, str):
            return HttpResponse(_("You should specify a message"), status=400)

        print("*."*10, "sending to bots is starting")
        # source: https://stackoverflow.com/a/21945663/10891757
        thread = threading.Thread(target=send_to_bots,
                                  args=(message,),
                                  kwargs={'bot_username': bot_username})
        thread.setDaemon(True)
        thread.start()
        print("*."*10, "sending to bots is done")
        messages.success(request, _(
            'message is being broadcasted, it may take some time'))
        return redirect('broadcast')

    return HttpResponse(_("Method not allowed"), status=405)
