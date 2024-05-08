from rest_framework import serializers
from productapp.serializers import ProductSerializer
from orderapp.models import (Order,
                             OrderDetails,
                             OrderStatus,
                             )
from productapp.models import Product
from userapp.models import UserProfile


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
    product_write_only = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True,
                                                            required=False, source='product')  # Переименовано поле
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
