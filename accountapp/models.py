from django.db import models
from userapp.models import UserProfile


class Account(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    account_number = models.CharField(unique=True)
    balance = models.FloatField(default=12100.09)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Account {self.account_number}"
