
from django.urls import path
from . import views

urlpatterns = [
    path('', views.AddressList.as_view(), name='address'),
    path('<int:_id>/', views.AddressDetails.as_view(), name='address_details'),
]
