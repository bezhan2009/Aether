from django.db import models
from django.contrib.auth.models import User
from django.urls import path, include
from .views import ping


urlpatterns = [
    path('ping/', path, name='ping'),
]
