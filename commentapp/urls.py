from django.urls import path
from . import views

urlpatterns = [
    path('<int:product_id>/', views.CommentList.as_view(), name='comment'),
    path('<int:comment_id>/detail/', views.CommentDetail.as_view(), name='comment_detail'),
]
