from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def schedual(request):
    # TODO: implement schdualed tasks: https://stackoverflow.com/a/71758288/10891757
    # https://testdriven.io/blog/django-celery-periodic-tasks/
    return render(request, "schedual/index.html")
