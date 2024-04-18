from django.urls import path
from . import views

urlpatterns = [
    path('account/', views.AccountList.as_view(), name='Account_list'),
    path('account/<int:_id>/', views.AccountDetails.as_view(), name='Account_detail'),
]
