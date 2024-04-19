from django.urls import path
from . import views

urlpatterns = [
    path('', views.AccountList.as_view(), name='Account_list'),
    path('<int:_id>/', views.AccountDetails.as_view(), name='Account_detail'),
]
