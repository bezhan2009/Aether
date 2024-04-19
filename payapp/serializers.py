from rest_framework import serializers
from .models import Payment
from accountapp.serializers import AccountSerializer
from orderapp.serializers import OrderDetailsSerializer
from userapp.models import UserProfile


class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)
    order = OrderDetailsSerializer()
    account = AccountSerializer()

    class Meta:
        model = Payment
        fields = '__all__'
