from django.contrib import admin
from .models import Product, OrderDetails, Payment, Address, Category, OrderStatus, Review, Comment

admin.site.register(Review)
admin.site.register(Comment)
