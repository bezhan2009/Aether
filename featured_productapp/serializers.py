from rest_framework import serializers

from featured_productapp.models import FeaturedProduct


class FeaturesProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeaturedProduct
        fields = '__all__'
