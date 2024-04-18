from django.db import models
from django.contrib.auth.models import User
from django.urls import path, include
from .views import UserProfileDetails, UserProfileList

urlpatterns = [
    path('', UserProfileList.as_view(), name='user_list'),
    path('details/', UserProfileDetails.as_view(), name='user_profile_details'),
]
