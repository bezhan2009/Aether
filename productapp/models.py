from django.db import models
from userapp.models import UserProfile


class Account(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    account_number = models.CharField(unique=True)
    balance = models.FloatField(default=12100.09)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Account {self.account_number}"


class Category(models.Model):
    category_name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.category_name


class Product(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='categories')
    title = models.CharField(max_length=100)
    description = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.FloatField()
    amount = models.IntegerField()
    default_account = models.ForeignKey(Account, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    views = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="product_images/")

    def __str__(self):
        return f"Image for {self.product.title}"
