from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.fields import ListField, CharField
from Aether.models import *


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'password', 'age', 'is_admin']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        name = validated_data.get('username', None)
        if UserProfile.objects.filter(username=name).exists():
            self.errors['username'] = ['The username is already taken.']
            raise serializers.ValidationError('The username is already taken. ')

        user_password = validated_data.get('password', None)
        hashed_password = make_password(user_password)
        validated_data['password'] = hashed_password

        return super(UserProfileSerializer, self).create(validated_data)


class ProductImageSerializer(serializers.ModelSerializer):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="product_images/")

    class Meta:
        model = ProductImage
        fields = ['image']


class ProductSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(),
                                              required=False)  # Делаем поле user необязательным

    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'user', 'category', 'title', 'description', 'price', 'amount', 'images']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class AccountSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(),
                                              required=False)  # Делаем поле user необязательным

    class Meta:
        model = Account
        fields = '__all__'


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
    product = serializers.CharField(source='product.name', read_only=True)
    address = serializers.CharField(source='address.address', read_only=True)

    class Meta:
        model = OrderDetails
        fields = '__all__'


class OrderDetailsNewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(),
                                              required=False)  # Делаем поле user необязательным
    product_s = serializers.CharField(source='product.name', read_only=True)
    address_s = serializers.CharField(source='address.address', read_only=True)
    product = ProductSerializer()

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


class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)
    order = OrderDetailsSerializer()
    account = AccountSerializer()

    class Meta:
        model = Payment
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), required=False)
    product = ProductSerializer()

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
