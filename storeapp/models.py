from django.db import models
from userapp.models import UserProfile


class Store(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    hash_password = models.CharField(max_length=100)
    ownerId = models.IntegerField(unique=True)
    owner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)

    def __str__(self):
        return self.name
