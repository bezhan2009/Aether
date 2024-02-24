from django.contrib import admin
from .models import UserProfile, Product, OrderDetails, Payment, Address, Category, OrderStatus

admin.site.register(UserProfile)
admin.site.register(Product)
admin.site.register(OrderDetails)
admin.site.register(Payment)
admin.site.register(OrderStatus)
admin.site.register(Address)
admin.site.register(Category)
