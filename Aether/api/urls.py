
from django.urls import path
from . import views
from .views import *
from Aether.views import *

urlpatterns = [
    path('products/', views.ProductList.as_view(), name='products'),
    path('products/<int:_id>/', views.ProductDetail.as_view(), name='product_detail'),
    path('products/<int:user_id>/user/', views.ProductUser.as_view(), name='product_user'),

    path('orders/', views.OrderList.as_view(), name='orders'),
    path('orders/<int:_id>/', views.OrderDetail.as_view(), name='order_detail'),
    path('payment/', views.OrderPaid.as_view(), name='Payment'),
    path('pay_order/<int:_id>/', views.OrderPay.as_view(), name='order_pay'),
    path('order_status/', views.OrderStatusList.as_view(), name='order_status'),
    path('payment/<int:_id>/', views.PayMentDetail.as_view(), name='payment'),

    path('address/', views.AddressList.as_view(), name='address'),
    path('address/<int:_id>/', views.AddressDetails.as_view(), name='address_details'),

    path('comment/<int:product_id>/', views.CommentList.as_view(), name='comment'),
    path('comment/<int:comment_id>/detail/', views.CommentDetail.as_view(), name='comment_detail'),

    path('category/', views.CategoryList.as_view(), name='category'),
    path('category/<int:_id>/', views.CategoryDetails.as_view(), name='category_detail'),

    path('account/', views.AccountList.as_view(), name='Account_list'),
    path('account/<int:_id>/', views.AccountDetails.as_view(), name='Account_detail'),

    path('review/<int:product_id>/', views.ReviewList.as_view(), name='review_list'),
    path('review/<int:_id>/detail/', views.ReviewDetail.as_view(), name='review_detail'),

    path('user/', views.UserProfileDetails.as_view(), name='user_profile_details'),

    path('about_us/', views.AboutUs.as_view(), name="About us")
]

'''{
    "user": 1,
    "title": "test",
    "description": "test_description",
    "price": 10.00,
    "amount": 3
}'''
