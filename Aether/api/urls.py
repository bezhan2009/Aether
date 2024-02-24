from django.contrib import admin
from django.urls import path
from Aether.api import views
from . import views
from .views import ProductDetail, ProductList, OrderDetail, OrderList, UserProfileAuthorization
from Aether.views import *
from django.contrib.auth.models import User

urlpatterns = [
    path('ping', ping, name='ping'),
    path('products/', ProductList.as_view(), name='products'),
    path('products/<int:_id>', views.ProductDetail.as_view(), name='product_detail'),

    path('orders', views.OrderList.as_view(), name='orders'),
    path('orders/<int:_id>', views.OrderDetail.as_view(), name='order_detail'),
    path('pay_order/<int:_id>', views.OrderPay.as_view(), name='order_pay'),
    path('order_status', views.OrderStatusList.as_view(), name='order_status'),
    path('payment/<int:_id>', views.PayMentDetail.as_view(), name='payment'),

    path('address', views.AddressList.as_view(), name='address'),

    path('category', views.CategoryList.as_view(), name='category'),
    path('category/<int:_id>', views.CategoryDetails.as_view(), name='category_detail'),

    path('account', views.AccountList.as_view(), name='Account_list'),
    path('account/<int:_id>', views.AccountDetails.as_view(), name='Account_detail'),
    path('review', views.ReviewList.as_view(), name='review_list'),
    path('review/<int:_id>', views.ReviewDetail.as_view(), name='review_detail'),

    path('user/<int:_id>', views.UserProfileDetails.as_view(), name='user_profile_details'),
]

'''{
    "user": 1,
    "title": "test",
    "description": "test_description",
    "price": 10.00,
    "amount": 3
}'''