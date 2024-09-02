from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from storeapp.models import *


class StoreSerializer(serializers.ModelSerializer):
    ownerID = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)

    class Meta:
        model = Store
        fields = '__all__'
