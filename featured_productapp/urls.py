from django.urls import path
from .views import FeaturedProductsList, FeaturedProductDetail

urlpatterns = [
    path('', FeaturedProductsList.as_view(), name='featuredProductsList'),
    path('detail/<int:pk>', FeaturedProductDetail.as_view(), name='featuredProductsDetail'),
]
