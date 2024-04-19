from rest_framework import serializers
from accountapp.models import *


class AccountSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(),
                                              required=False)  # Делаем поле user необязательным

    class Meta:
        model = Account
        fields = '__all__'
