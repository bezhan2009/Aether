from rest_framework import serializers
from productapp.models import *
from categoryapp.serializers import CategorySerializer


class ProductImageSerializer(serializers.ModelSerializer):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="product_images/")

    class Meta:
        model = ProductImage
        fields = ['image']


class ProductSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'user', 'category', 'title', 'description', 'price', 'amount', 'images', 'default_account', "views"]


class ProductUpDateNewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)
    class Meta:
        model = Product
        fields = ['id', 'user', 'category', 'title', 'description', 'price', 'amount', 'images', 'default_account', "views"]


class ProductUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    price = serializers.FloatField(required=False)
    amount = serializers.IntegerField(required=False)
    default_account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False)
    is_deleted = serializers.BooleanField(required=False)

    def validate(self, data):
        # Your validation logic if needed
        return data


class ProductQuerySerializer(serializers.Serializer):
    show_own_products = serializers.BooleanField(default=False, help_text="Show own products or not")
    search = serializers.CharField(allow_blank=True, required=False, help_text="Search query")
    min_price = serializers.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2)
    max_price = serializers.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2)
    category = serializers.CharField(required=False)
