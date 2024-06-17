from django.urls import path
from .views import FeaturedProductsList

urlpatterns = [
    path('', FeaturedProductsList.as_view(), name='featuredProductsList'),
]
