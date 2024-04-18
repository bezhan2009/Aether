from django.db import models
from django.contrib.auth.models import User

class UserProfile(User):
    age = models.IntegerField()
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} (Admin: {self.is_admin})"
