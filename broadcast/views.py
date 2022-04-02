import os
from bots.models import Bot

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from broadcast.broadcast import send_to_bot


def send_to_bots(message, bot_username):
    bots = Bot.objects.all()
    if bot_username:
        bots = bots.filter(username=bot_username)
    print("-_"*20)
    print(message)
    print("-_"*20)
    for bot in bots:
        print("sending to", bot.username)
        # send_to_bot(message, bot.username)


@login_required
def broadcast(request):
    if request.method == "POST":
        password = request.POST.get("password")
        message = request.POST.get("message")
        bot_username = request.POST.get("bot")

        if password != os.environ.get("password"):
            pass
        if not message and not isinstance(message, str):
            return HttpResponse(_("You should specify a message"), status=400)

        send_to_bots(message, bot_username=bot_username)
        messages.success(request, _('message is being broadcasted, it may take some time'))
        return redirect('broadcast')

    if request.method == "GET":
        return render(request, "broadcast/index.html", context={ "bots": Bot.objects.all() })

    return HttpResponse(_("Method not allowed"), status=405)
