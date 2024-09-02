from django.db import models
from storeapp.models import UserProfile
from accountapp.models import Account
from categoryapp.models import Category


# class Store(models.Model):
#     name = models.CharField(max_length=100)
#     description = models.TextField()
#     hash_password = models.CharField(max_length=100)
#     ownerId = models.IntegerField(unique=True)
#     owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     deleted_at = models.DateTimeField(null=True)
#
#     def __str__(self):
#         return self.name


class Product(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='categories')
    title = models.CharField(max_length=100)
    description = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.FloatField()
    amount = models.IntegerField()
    default_account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, default=None)
    is_deleted = models.BooleanField(default=False)
    views = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name='images')
    image = models.ImageField(upload_to="product_images/")

    def __str__(self):
        return f"Image for {self.product.title}"
