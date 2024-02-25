from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import ArrayField  # Import ArrayField


class UserProfile(User):
    age = models.IntegerField()
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} (Admin: {self.is_admin})"


class Category(models.Model):
    category_name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.category_name


class Address(models.Model):
    address_name = models.CharField(max_length=100)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.address_name


class Product(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='categories')
    title = models.CharField(max_length=100)
    description = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.FloatField()
    amount = models.IntegerField()
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="product_images/")

    def __str__(self):
        return f"Image for {self.product.title}"


class OrderStatus(models.Model):
    status_name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.status_name


class OrderDetails(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
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


class Account(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    account_number = models.CharField(unique=True)
    balance = models.FloatField(default=100.09)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Account {self.account_number}"


class Payment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    order = models.ForeignKey(OrderDetails, on_delete=models.CASCADE)
    amount = models.IntegerField()
    price = models.FloatField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    payed_at = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Payment for Order {self.order.id} by {self.user.username}"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    parent_id = models.IntegerField(null=True)
    comment_text = models.TextField()
    children = models.ManyToManyField('self', related_name='parent', blank=True)
