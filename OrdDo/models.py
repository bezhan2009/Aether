from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator


class Staff(User):
    default_account = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.username} (Default account: {self.default_account})"
