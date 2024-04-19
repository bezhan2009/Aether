from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import (MaxValueValidator,
                                    MinValueValidator
)
from userapp.models import UserProfile
from productapp.models import (
    Product,
    Account,
    Category
)
from orderapp.models import (OrderStatus,
                             OrderDetails,
                             Payment,
                             Address
                             )
from categoryapp.models import Category


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
