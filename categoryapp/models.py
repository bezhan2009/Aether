from django.db import models


class Category(models.Model):
    category_name = models.CharField(max_length=100)
    category = models.IntegerField(null=True)
    description = models.TextField()

    def __str__(self):
        return self.category_name
