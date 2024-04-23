"""
URL configuration for calorie_tricker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView, TokenObtainPairView
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.renderers import SwaggerUIRenderer

from Aether.views import ping

schema_view = get_schema_view(
    openapi.Info(
        title="Your API",
        default_version='v1',
        description="API description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@yourdomain.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('admin/', admin.site.urls),
    path('aether/', include('Aether.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='verify_refresh'),
    path('auth/sign-in/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    path('api/user/', include('userapp.urls')),
    path('api/products/', include('productapp.urls')),
    path('api/orders/', include('orderapp.urls')),
    path('api/account/', include('accountapp.urls')),
    path('api/address/', include('addressapp.urls')),
    path('api/payment/', include('payapp.urls')),
    path('api/category/', include('categoryapp.urls')),
    path('api/review/', include('reviewapp.urls')),
    path('api/comment/', include('commentapp.urls')),
]
