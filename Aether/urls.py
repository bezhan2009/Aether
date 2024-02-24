from django.db import models
from django.contrib.auth.models import User
from django.urls import path, include

from Aether import views

urlpatterns = [
    path('ping', views.ping, name='ping'),
    path('api/', include('Aether.api.urls'))
]


"""
urlpatterns = [
    path('tasks/', TaskView.as_view(), name='tasks_list'),
    path('tasks/<int:task_id>/', TaskView.as_view(), name='task_detail'),
    path('tasks/<int:task_id>/details/', TaskView.as_view(), name='task_details'),
]
"""