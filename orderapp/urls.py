
from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.OrderList.as_view(), name='orders'),
    path('orders/<int:_id>/', views.OrderDetail.as_view(), name='order_detail'),
    path('payment/', views.OrderPaid.as_view(), name='Payment'),
    path('pay_order/<int:_id>/', views.OrderPay.as_view(), name='order_pay'),
    path('order_status/', views.OrderStatusList.as_view(), name='order_status'),
    path('payment/<int:_id>/', views.PayMentDetail.as_view(), name='payment'),
]
