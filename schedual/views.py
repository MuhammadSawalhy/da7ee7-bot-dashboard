from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def schedual(request):
    return render(request, "schedual/index.html")
