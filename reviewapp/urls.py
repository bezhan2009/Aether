from django.urls import path
from . import views


urlpatterns = [
    path('<int:product_id>/', views.ReviewList.as_view(), name='review_list'),
    path('<int:_id>/detail/', views.ReviewDetail.as_view(), name='review_detail'),
]
