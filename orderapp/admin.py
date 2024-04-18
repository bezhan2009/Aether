from django.contrib import admin
from .models import Product, OrderDetails, Payment, Address, Category, OrderStatus

admin.site.register(OrderStatus)
admin.site.register(OrderDetails)
admin.site.register(Payment)
admin.site.register(Address)