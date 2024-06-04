from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProductList.as_view(), name='products'),
    path('<int:_id>/', views.ProductDetail.as_view(), name='product_detail'),
    path('<int:user_id>/user/', views.ProductUser.as_view(), name='product_user'),
]
