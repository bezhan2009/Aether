from rest_framework import serializers
from .models import Review
from userapp.models import UserProfile
from productapp.models import Product


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False)

    class Meta:
        model = Review
        fields = '__all__'
