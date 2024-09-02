from django.db import models
from django.contrib.auth.models import User
from django.urls import path, include
from .views import StoreDetails, StoreList

urlpatterns = [
    path('sign-up/', StoreList.as_view(), name='user_list'),
    path('user/details/', StoreDetails.as_view(), name='user_profile_details'),
]
