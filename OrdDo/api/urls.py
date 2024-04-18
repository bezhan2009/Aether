
from django.urls import path
from . import views
from .views import *
from Aether.views import *

urlpatterns = [
    path('about_us/', views.AboutUs.as_view(), name="About us")
]

'''{
    "user": 1,
    "title": "test",
    "description": "test_description",
    "price": 10.00,
    "amount": 3
}'''
