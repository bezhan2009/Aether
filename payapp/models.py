from django.db import models
from django.utils import timezone
from userapp.models import UserProfile
from productapp.models import Account


class Payment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    order = models.ForeignKey('orderapp.OrderDetails', on_delete=models.CASCADE)
    amount = models.IntegerField()
    price = models.FloatField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    payed_at = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Payment for Order {self.order.id} by {self.user.username}"
