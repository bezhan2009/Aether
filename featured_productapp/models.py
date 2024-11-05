from django.db import models

from productapp.models import Product
from userapp.models import User


class FeaturedProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
