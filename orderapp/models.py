from django.db import models
from django.utils import timezone
from userapp.models import UserProfile
from productapp.models import (
    Product,
    Account,
    Category
)
from addressapp.models import Address
from payapp.models import Payment


class OrderStatus(models.Model):
    status_name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.status_name


class OrderDetails(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.FloatField(null=True, blank=True)
    quantity = models.IntegerField(default=1)
    is_deleted = models.BooleanField(default=False)
    order_date = models.DateTimeField(default=timezone.now)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.title} - {self.quantity} units"


class Order(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)
    order_details = models.ForeignKey(OrderDetails, on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False, null=True)
    is_in_the_card = models.BooleanField(default=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"
