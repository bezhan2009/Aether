from django.urls import path
from . import views


urlpatterns = [
    path('', views.OrderPaid.as_view(), name='Payment'),
    path('pay_order/<int:_id>/', views.OrderPay.as_view(), name='order_pay'),
    path('<int:_id>/', views.PayMentDetail.as_view(), name='payment'),
]
