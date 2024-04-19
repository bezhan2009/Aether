from django.contrib import admin
from .models import OrderDetails, OrderStatus

admin.site.register(OrderStatus)
admin.site.register(OrderDetails)
