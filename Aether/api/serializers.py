from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from Aether.models import *
from productapp.serializers import (ProductSerializer,
                                    ProductQuerySerializer,
                                    ProductImage,
                                    ProductUpDateNewSerializer,
                                    AccountSerializer
                                )


class AddressSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(),
                                              required=False)  # Делаем поле user необязательным

    class Meta:
        model = Address
        fields = '__all__'


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatus
        fields = '__all__'


class OrderDetailsSerializer(serializers.ModelSerializer):
    address = serializers.CharField(source='address.address', read_only=True)

    class Meta:
        model = OrderDetails
        fields = '__all__'


class OrderDetailsNewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)
    product_write_only = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True, required=False, source='product')  # Переименовано поле
    address_s = serializers.CharField(source='address.address', read_only=True)
    product_s = serializers.CharField(source='product.name', read_only=True)
    product_detail = ProductSerializer(source='product', read_only=True)  # Изменено имя поля для ProductSerializer

    class Meta:
        model = OrderDetails
        fields = '__all__'


class OrderDetailsFCSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)

    class Meta:
        model = OrderDetails
        fields = '__all__'


class OrderDetailsAloneSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(),
                                              required=False)  # Делаем поле user необязательным
    # product_s = serializers.CharField(source='product.name', read_only=True)
    # address_s = serializers.CharField(source='address.address', read_only=True)

    class Meta:
        model = OrderDetails
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    status = OrderStatusSerializer()
    order_details = OrderDetailsNewSerializer()  # Убрали many=True здесь

    class Meta:
        model = Order
        fields = '__all__'


class OrderNewSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderDetails
        fields = ('quantity',)


class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)
    order = OrderDetailsSerializer()
    account = AccountSerializer()

    class Meta:
        model = Payment
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False)

    class Meta:
        model = Review
        fields = '__all__'


class CommentChildrenSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    comment_text = serializers.CharField()
    parent_id = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = ['id', 'comment_text', 'parent_id']


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False)

    class Meta:
        model = Comment
        fields = '__all__'


class CommentMainSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    comment_text = serializers.CharField()
    parent_id = serializers.IntegerField()
    children = CommentChildrenSerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'comment_text', 'parent_id', 'children']


class ProductUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    price = serializers.IntegerField(required=False)
    amount = serializers.IntegerField(required=False)

    def validate(self, data):
        # Ensure that only specified fields are allowed
        allowed_fields = {'title', 'description', 'price', 'amount'}
        for key in data.keys():
            if key not in allowed_fields:
                raise serializers.ValidationError(f"Field '{key}' is not allowed for update.")
        return data


class ProductQuerySerializer(serializers.Serializer):
    show_own_products = serializers.BooleanField(default=False, help_text="Show own products or not")
    search = serializers.CharField(allow_blank=True, required=False, help_text="Search query")
    min_price = serializers.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2)
    max_price = serializers.DecimalField(required=False, min_value=0, max_digits=10, decimal_places=2)
    category = serializers.CharField(required=False)
