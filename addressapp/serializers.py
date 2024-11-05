from rest_framework import serializers
from .models import Address
from userapp.models import UserProfile


class AddressSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(),
                                              required=False)  # Делаем поле user необязательным

    class Meta:
        model = Address
        fields = '__all__'