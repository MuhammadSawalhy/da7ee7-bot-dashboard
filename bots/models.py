import re
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def bot_username_validator(username):
    if not re.match(r'@\w+', username):
         raise ValidationError(
            _('%(username)s is not a valid bot username'),
            params={'username': username},
        )


class Bot(models.Model):
    username = models.CharField(max_length=50, unique=True, validators=[
                                bot_username_validator])
    token = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.username
