
from django.urls import path
from . import views


urlpatterns = [
    path('', views.OrderList.as_view(), name='orders'),
    path('<int:_id>/', views.OrderDetail.as_view(), name='order_detail'),
    path('status/', views.OrderStatusList.as_view(), name='order_status'),
]


