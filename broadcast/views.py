import os
import re
import glob
from bots.models import Bot
from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from broadcast.broadcast import send_to_bots_in_background, is_broadcasting, cancel_broadcasting


def write_image(image):
    for prev_img_path in glob.glob('staticfiles/telegram-image-to-send-*.png'):
        print("prev image:", prev_img_path)
        os.remove(prev_img_path)
    now = datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    image_file_name = f"telegram-image-to-send-{now}.png"
    print("next image:", image_file_name)
    image_path = settings.BASE_DIR / "staticfiles" / image_file_name
    with open(image_path, 'wb+') as f:
        for chunk in image.chunks():
            f.write(chunk)
    if settings.IS_LOCALHOST:
        return None
    return f"{os.environ.get('SITE_URL')}/static/{image_file_name}"


def check_message(request, message, *, image):
    if not message and not image:
        messages.error(request, _("You should specify a message"))
        return redirect('broadcast')
    if image and len(message) > 1024:
        messages.error(request, _(
            "Image caption should not excceed 1024 chars"))
        return redirect('broadcast')
    if not image and len(message) > 4096:
        messages.error(request, _(
            "Message is too long to send, please send a message less than 4096 characters"))
        return redirect('broadcast')


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
        password = request.POST.get("password")
        bots_usernames = request.POST.getlist("bot")
        message = request.POST.get("message") or ""
        image = request.FILES.get("image") or None
        if image:
            image = write_image(image)
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
        if response := check_message(request, message=message, image=image):
            return response

        if not is_broadcasting():
            send_to_bots_in_background(
                message, image=image, bots_usernames=bots_usernames)
        else:
            messages.error(request, _(
                'Another broadcasting is in progress, please wait!'))

        return redirect('broadcast')

    return HttpResponse(_("Method not allowed"), status=405)


@csrf_exempt
def cancel(request):
    if is_broadcasting():
        cancel_broadcasting()
        messages.success(request, _(
            'the previous running broadcasting was successfully canceled'))
    else:
        messages.error(request, _(
            'no running broadcasting exists'))
    return redirect('broadcast')
