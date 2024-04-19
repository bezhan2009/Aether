from django.db import models
from django.contrib.auth.models import User
from productapp.models import Product


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    parent_id = models.IntegerField(null=True)
    comment_text = models.TextField()
