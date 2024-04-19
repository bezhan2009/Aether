from django.shortcuts import get_object_or_404
from rest_framework import permissions
from drf_yasg import openapi
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from django.db import transaction
from .serializers import *
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from django.db.models import Q
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from utils.tokens import get_user_id_from_token
from userapp.serializers import UserProfileSerializer
from productapp.serializers import CategorySerializer
from productapp.serializers import (ProductSerializer,
                                    ProductUpdateSerializer,
                                    ProductQuerySerializer,
                                    ProductImage,
                                    ProductUpDateNewSerializer
                                    )

from utils.commentTree import build_comment_tree

logger = logging.getLogger('django')


class ProductDetail(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    def get_object(self, _id):
        try:
            user_id = get_user_id_from_token(self.request)
            user_profile = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            return get_object_or_404(Product, id=_id)
        return get_object_or_404(Product, id=_id, user=user_profile)

    @transaction.atomic
    def get(self, request, _id):
        try:
            product = self.get_object(_id)
        except Http404:
            logger.error(f"Product with ID {_id} not found.")
            return Response({"message": f"Product Not Found"}, status=404)

        serializer = ProductSerializer(product)
        product.views += 1
        product.save()
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=ProductUpdateSerializer,
    )
    def put(self, request, _id):
        product = self.get_object(_id)
        serializer = ProductUpDateNewSerializer(product, data=request.data, partial=True)

        if serializer.is_valid():
            cover_imgs = request.data.get('cover_img')

            # Удаляем старые изображения перед добавлением новых
            product.images.all().delete()

            if cover_imgs:
                for cover_img in cover_imgs:
                    ProductImage.objects.create(product=product, image=cover_img)

            serializer.validated_data["category"] = product.category
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ], )
    def delete(self, request, _id):
        try:
            product = self.get_object(_id)
            logger.info(f"Attempting to delete product with ID {_id}.")
        except Http404:
            logger.warning(f"Failed to delete product. Product with ID {_id} not found.")
            return Response({"message": "Product Not Found"}, status=404)

        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)

        if not product.is_deleted and user_profile.is_admin:
            product.is_deleted = True
            product.save()
            logger.info(f"Product with ID {_id} marked as deleted.")
            return Response({"message": "The product has been successfully removed"}, status=200)
        else:
            logger.warning(
                f"Failed to delete product. Product with ID {_id} has already been deleted or user is not an admin.")
            return Response({"message": "Product has already been deleted or unauthorized access."}, status=404)


class ProductList(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        query_serializer=ProductQuerySerializer(),
    )
    def get(self, request):
        query_serializer = ProductQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        show_own_products = query_serializer.validated_data.get('show_own_products', False)
        search_query = query_serializer.validated_data.get('search', None)
        min_price = query_serializer.validated_data.get('min_price')
        max_price = query_serializer.validated_data.get('max_price')
        categories = query_serializer.validated_data.get('category')

        try:
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)
            if 2 + 2 == 4:
                products = Product.objects.filter(is_deleted=False, amount__gt=0)
            if user_profile.is_admin and not show_own_products:
                products = products.filter(is_deleted=False, amount__gt=0)
            elif user_profile.is_admin and show_own_products:
                products = products.filter(user=user_profile, is_deleted=False, amount__gt=0)

            if search_query:
                products = products.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

            if min_price is not None:
                products = products.filter(price__gte=min_price)
            if max_price is not None:
                products = products.filter(price__lte=max_price)
            if categories:
                try:
                    category = Category.objects.get(id=categories)
                    products = products.filter(category=category)
                except Category.DoesNotExist:
                    return Response({"message": "Category not found"}, status=404)

            products = products.order_by('-views')[:30]
            serializer = ProductSerializer(products, many=True)

            return Response(serializer.data, status=200)

        except UserProfile.DoesNotExist:
            products = Product.objects.filter(is_deleted=False)

            if search_query:
                products = products.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

            if min_price is not None:
                products = products.filter(price__gte=min_price)
            if max_price is not None:
                products = products.filter(price__lte=max_price)
            if categories:
                try:
                    category = Category.objects.get(id=categories)
                    products = products.filter(category=category)
                except Category.DoesNotExist:
                    return Response({"message": "Category not found"}, status=404)

            products = products.order_by('-views')[:30]
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=200)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the category"),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Title of the item"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description of the item"),
                'price': openapi.Schema(type=openapi.TYPE_INTEGER, description="Price of the item"),
                'amount': openapi.Schema(type=openapi.TYPE_INTEGER, description="Amount of the item"),
                'default_account': openapi.Schema(type=openapi.TYPE_INTEGER, description="Default account for money")
            },
            required=['category', 'title', 'description', 'price', 'amount']
        ),
        security=[],
    )
    @transaction.atomic
    def post(self, request):
        try:
            # Get the array of images from the request data
            cover_imgs = request.data.get('cover_img')
            if cover_imgs:
                pass
            else:
                cover_imgs = []
            # Get the user profile based on the token or however you identify the user
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)

            # Check if the user is an admin
            if not user_profile.is_admin:
                raise PermissionDenied("You don't have permission to create a product.")
            if not Account.objects.filter(user=user_profile).first():
                raise PermissionDenied("You are have not account please create account and replay.")

            data = {
                'user': user_profile,
                'category': request.data.get('category'),
                'title': request.data.get('title'),
                'description': request.data.get('description'),
                'price': request.data.get('price'),
                'amount': request.data.get('amount'),
                'default_account': request.data.get('default_account')
            }

            # Log request data
            logger.info(f"Request data - User: {user_profile.username}, Data: {data}, Cover Images: {cover_imgs}")

            # Create a ProductSerializer instance with the data and cover_imgs
            try:
                account = Account.objects.filter(user=user_profile).first()
                if account:
                    if data["default_account"] is None:
                        data["default_account"] = account.id
                    else:
                        try:
                            account = Account.objects.get(id=data["default_account"], user=user_profile)
                        except Account.DoesNotExist:
                            user_id = get_user_id_from_token(request)
                            logger.warning(
                                f"Failed to retrieve products for user with ID {user_id}. Account Not Found.")
                            data["default_account"] = account.id
            except Account.DoesNotExist:
                user_id = get_user_id_from_token(request)
                logger.warning(f"Failed to create product for user with ID {user_id}. Account Not Found.")
                return Response({"warning": "You are have not account please create account and replay."},
                                status=status.HTTP_404_NOT_FOUND)
            serializer = ProductSerializer(data=data)
            if serializer.is_valid():
                # Save the product instance
                product = serializer.save()

                # Save each image in the cover_imgs array
                for cover_img in cover_imgs:
                    ProductImage.objects.create(product=product, image=cover_img)

                # Log information including user details, product ID, and image details
                logger.info(
                    f"Product created successfully. User: {user_profile.username}, Product ID: {product.id}, Cover "
                    f"Images: {cover_imgs}")

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Invalid data provided: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as pd:
            logger.warning("Permission Denied: " + str(pd) + "")
            return Response({"Permission Denied": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, _id):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)
        return get_object_or_404(Order, id=_id, user=user_profile, is_paid=False)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description="Amount of the item", default=1)
            },
            required=['quantity']
        ),
        security=[],
    )
    @transaction.atomic
    def put(self, request, _id):
        try:
            order = self.get_object(request, _id)
            logger.info(f"Attempting to update order detail with ID {_id}.")
        except UserProfile.DoesNotExist:
            user_id = get_user_id_from_token(request)
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. User profile not found.")
            return Response({"message": "You have not registered"}, status=status.HTTP_404_NOT_FOUND)
        except Http404:
            logger.warning(f"Failed to update order detail. Order detail with ID {_id} not found.")
            return Response({"message": "Order Not Found."}, status=404)

        serializer = OrderNewSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            order.order_details.quantity += serializer.validated_data["quantity"]
            order.order_details.price = order.order_details.quantity * order.order_details.product.price
            order.order_details.save()
            serializer.save()
            logger.info(f"Order detail with ID {_id} updated successfully.")
            return Response({"message": "Order updated successfully"}, status=200)
        logger.error(f"Failed to update order detail with ID {_id}: {serializer.errors}")
        return Response(serializer.errors, status=401)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def delete(self, request, _id):
        try:
            order = self.get_object(request, _id)
        except Http404:
            user_id = get_user_id_from_token(request)
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. order not found.")
            return Response({"message": "Order Not Found or this order has payed"}, status=status.HTTP_404_NOT_FOUND)
        except UserProfile.DoesNotExist:
            user_id = get_user_id_from_token(request)
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. User profile not found.")
            return Response({"message": "You have not registered"}, status=status.HTTP_404_NOT_FOUND)
        except OrderDetails.DoesNotExist:
            logger.warning(f"Failed to delete order detail. Order detail with ID {_id} not found.")
            return Response({"message": "Order Not Found"}, status=status.HTTP_404_NOT_FOUND)

        order.order_details.is_deleted = True
        order.order_details.save()

        logger.info(f"Order detail with ID {_id} marked as deleted.")
        return Response({"message": "Order has been successfully removed"}, status=status.HTTP_200_OK)


class OrderPaid(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get(self, request):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id, is_admin=False)
        payments = Payment.objects.filter(user=user_profile, is_deleted=False)
        if payments:
            serializer = PaymentSerializer(payments, many=True)
            return Response(serializer.data, status=200)
        else:
            return Response({"message": "You don't have any payment"}, status=404)


class PayMentDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def delete(self, request, _id):
        user_id = get_user_id_from_token(request)
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            payment = Payment.objects.get(id=_id, user=user_profile, is_deleted=False)
        except Payment.DoesNotExist:
            logger.warning(f"Failed to delete payment. Payment with ID {_id} not found.")
            return Response({"message": f"Payment with ID {_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        if not payment.is_deleted:
            payment.is_deleted = True
            payment.save()
            logger.info(f"Payment with ID {_id} marked as deleted.")
        else:
            logger.warning(f"Failed to delete payment. Payment with ID {_id} has already been deleted.")

        serializer = PaymentSerializer({"message": "Payment has been successfully removed"}, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderPay(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get_order(self, _id, request):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)
        return get_object_or_404(Order, id=_id, is_paid=False, user=user_profile)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'account_number': openapi.Schema(type=openapi.TYPE_STRING, description="Amount of the item",
                                                 default="1")
            },
        ),
        security=[],
    )
    @transaction.atomic
    def post(self, request, _id):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)

        try:
            order = self.get_order(_id, request)
            logger.info(f"Attempting to process payment for order with ID {_id}.")
        except Http404:
            logger.warning(f"Failed to process payment. Order with ID {_id} not found.")
            return Response({"message": "Order not found."}, status=404)

        try:
            order_details = OrderDetails.objects.get(id=order.order_details.id)
        except OrderDetails.DoesNotExist:
            logger.warning(f"Failed to process payment. Order details not found for order with ID {_id}.")
            return Response({"message": "Order details not found."}, status=404)

        _account_number = request.data.get('account_number')
        if not _account_number:
            logger.warning(f"Failed to process payment. Account number not found.")
            return Response({"message": "Account number not provided."}, status=404)
        try:
            account = Account.objects.get(account_number=_account_number, user=user_profile)
        except Account.DoesNotExist:
            accounts = Account.objects.filter(user=user_profile)
            if accounts.exists():
                for _account in accounts:
                    if _account.balance >= order_details.price:
                        _account.balance -= order_details.price
                        account = _account
                        break
            else:
                user_id = get_user_id_from_token(request)
                logger.warning(f"Failed to retrieve products for user with ID {user_id}. Account Not Found.")
                return Response({"warning": "You are have not account please create account and replay."},
                                status=status.HTTP_404_NOT_FOUND)
        try:
            user_profile = UserProfile.objects.get(id=order.user.id)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to process payment. User profile not found for user with ID {order.user.id}.")
            return Response({"message": f"User profile not found for user with ID {order.user.id}."}, status=404)
        if account and hasattr(account, 'balance') and account.balance >= order_details.price:
            account.balance -= order_details.price
            try:
                product = Product.objects.get(id=order_details.product.id)
            except Product.DoesNotExist:
                logger.warning(f"Failed to process payment. Product not found.")
                return Response({"message": "Product not found."}, status=404)

            if product.default_account:
                account_user_product = Account.objects.get(id=product.default_account.id)
            else:
                user_product = UserProfile.objects.get(id=product.user.id)
                try:
                    account_user_product = Account.objects.filter(user=user_product).first()
                except Account.DoesNotExist:
                    logger.warning(f"Failed to process payment. Account not found.")
                    return Response({"message": "Account not found."}, status=404)

            account_user_product.balance += order_details.price
            order.is_paid = True
            order.is_in_the_card = False
            order.status = OrderStatus.objects.get(id=3)
            payment = Payment.objects.create(
                order=order_details,
                account=account,
                user=user_profile,
                amount=order_details.quantity,
                price=order_details.price
            )

            payment.save()
            order.save()
            account.save()
            logger.info(f"Payment processed successfully for order with ID {_id}.")
            serializer = PaymentSerializer(payment)
            return Response(serializer.data, status=200)
        else:
            logger.warning(f"Failed to process payment. Insufficient funds for order with ID {_id}.")
            return Response({"message": "You do not have enough funds to make the purchase"}, status=401)


class OrderList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            if user_profile.is_admin:
                product_orders = Order.objects.prefetch_related(
                    'status',
                    'order_details__product',
                    'order_details__address',
                ).filter(order_details__product__user=user_profile, order_details__is_deleted=False).distinct()
                serializer = OrderSerializer(product_orders, many=True)
                if not product_orders.exists():
                    return Response("No one has purchased your products yet.", status=status.HTTP_404_NOT_FOUND)
                logger.info(f"User with ID {user_id} retrieved their orders and product orders.")
                return Response(serializer.data, status=status.HTTP_200_OK)

            orders = Order.objects.prefetch_related(
                'status',
                'order_details__product',
                'order_details__address',
            ).filter(user=user_profile, order_details__is_deleted=False, is_in_the_card=True)
            serializer = OrderSerializer(orders, many=True)
            if not orders.exists():
                return Response({"message": "You have no orders yet."}, status=status.HTTP_404_NOT_FOUND)
            logger.info(f"User with ID {user_id} retrieved their orders.")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to retrieve orders for user with ID {user_id}. User profile not found.")
            return Response({"message": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Order.DoesNotExist:
            logger.warning(f"Failed to retrieve orders for user with ID {user_id}. Order not found.")
            return Response({"message": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.warning(f"Failed to retrieve orders for user with ID {user_id}. {str(e)}")
            return Response({"error": f"{str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the product"),
                'address': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the address"),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description="Quantity of the product"),
            },
            required=['product', 'address', 'quantity']
        ),
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    @transaction.atomic
    def post(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            if user_profile.is_admin:
                raise PermissionDenied("Admins are not allowed to create orders.")
        except PermissionDenied as pd:
            logger.warning(f"Permission Denied: {str(pd)}")
            return Response({"error": str(pd)}, status=status.HTTP_403_FORBIDDEN)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to retrieve user with ID {user_id}. User profile not found.")
            return Response({"message": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Internal Server Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = OrderDetailsNewSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data["product"].id
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                logger.error(f"Product with ID {product_id} not found.")
                return Response({"message": f"Product with ID {product_id} not found."}, status=404)
            address_instance = serializer.validated_data['address']
            address = address_instance
            try:
                address = Address.objects.get(id=address.id, user=user_profile)
            except Address.DoesNotExist:
                logger.error(f"Address with ID {address.id} not found. Choosing another address...")

                addresses = Address.objects.filter(user=user_profile)
                if addresses.exists() and len(addresses) == 1:
                    address_instance = addresses[0]
                    logger.warning(f"The choice of another address was successfully")
                else:
                    addresses = Address.objects.filter(user=user_profile)
                    logger.error(f"Failed to find address for user with id {user_id}")
                    if addresses.exists():
                        return Response({
                            "message": f"Please choose another address"},
                            status=404)
                    else:
                        return Response({
                            "message": f"You do not have any Addresses. Please create an address then you can to order this product {product}"},
                            status=404)

            amount = serializer.validated_data['quantity']

            if amount > product.amount or amount <= 0:
                logger.warning(f"Insufficient stock for product with ID {product_id}.")
                return Response({"message": f"Insufficient stock for product with ID {product_id}."}, status=401)
            else:
                price = product.price * amount
                product.amount -= amount
                if product.amount == 0:
                    product.is_deleted = True
            order_details = OrderDetails.objects.create(
                product=product,
                price=price,
                quantity=amount,
                address=address_instance
            )

            order_status = OrderStatus.objects.get(id=1)

            order = Order.objects.create(
                user=user_profile,
                status=order_status,
                order_details=order_details
            )
            order_details.save()
            order.save()
            product.save()

            logger.info(f"User with ID {user_id} placed a new order with ID {order.id}.")
            return Response({"message": "Order created successfully"}, status=200)

        logger.error(f"Invalid data received while creating a new order: {serializer.errors}")
        return Response(serializer.errors, status=401)


class UserProfileDetails(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_user(self, _id):
        return get_object_or_404(UserProfile, id=_id)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user = self.get_user(user_id)
            logger.info(f"User with ID {user_id} retrieved successfully.")
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to retrieve user. User with ID {user_id} not found.")
            return Response({"message": "User Not Found"}, status=404)

        serializer = UserProfileSerializer(user, many=False)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['username', 'password']
        ),
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def put(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user = self.get_user(user_id)
            logger.info(f"Attempting to update user with ID {user_id}.")
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to update user. User with ID {user_id} not found.")
            return Response({"message": "User Not Found."}, status=404)

        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if 'password' in request.data or 'is_deleted' in request.data or 'is_superuser' in request.data:
            return Response({"message": "Changing password, is_superuser is not allowed."}, status=403)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User with ID {user_id} updated successfully.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to update user with ID {user_id}: {serializer.errors}")
        return Response(serializer.errors, status=401)


class CategoryList(APIView):
    def get(self, request):
        category = Category.objects.all()
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'category_name': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['category_name', 'description']
        ),
    )
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"New category created with ID {serializer.data.get('id')}.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to create a new category: {serializer.errors}")
        return Response(serializer.errors, status=401)


class CategoryDetails(APIView):
    def get_object(self, _id):
        return get_object_or_404(Category, id=_id)

    def get(self, request, _id):
        try:
            category = self.get_object(_id)
            serializer = CategorySerializer(category)
        except Http404:
            return Response({"message": "Category Not Found"}, status=404)
        return Response(serializer.data, status=200)

    def put(self, request, _id):
        try:
            category = self.get_object(_id)
        except Category.DoesNotExist:
            logger.warning(f"Failed to update category. Category with ID {_id} not found.")
            return Response({"message": "Category Not Found"}, status=404)

        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Category with ID {_id} updated successfully.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to update category with ID {_id}: {serializer.errors}")
        return Response(serializer.errors, status=401)

    def delete(self, request, _id):
        try:
            category = self.get_object(_id)
        except Category.DoesNotExist:
            logger.warning(f"Failed to delete category. Category with ID {_id} not found.")
            return Response({"message": "Category Not Found"}, status=404)

        category.is_deleted = True
        logger.info(f"Category with ID {_id} marked as deleted.")
        return Response({"message": "Category has been successfully removed."}, status=200)


class AddressList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get(self, request):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)
        try:
            address = Address.objects.filter(user=user_profile, is_deleted=False)
            serializer = AddressSerializer(address, many=True)
        except Address.DoesNotExist:
            logger.error(f"Address not found.")
            return Response({"message": f"You don't have any addresses."}, status=404)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'address_name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['address_name']
        ),
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)
            serializer.save(user=user_profile)
            logger.info(f"New address created with ID {serializer.data.get('id')} for user {user_id}.")
            return Response(serializer.data, status=200)
        else:
            logger.error(f"Failed to create a new address: {serializer.errors}")
            return Response(serializer.errors, status=400)


class AddressDetails(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, _id):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)
        return get_object_or_404(Address, user=user_profile, id=_id, is_deleted=False)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get(self, request, _id):
        try:
            address = self.get_object(request, _id)
            serializer = AddressSerializer(address, many=False)
            return Response(serializer.data, status=200)
        except Http404:
            logger.warning(f"Failed to retrieve address. Address with ID {_id} not found.")
            return Response({"message": "Address not found"}, status=404)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'address_name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['address_name']
        ),
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def put(self, request, _id):
        try:
            address = self.get_object(request, _id)
        except Http404:
            logger.warning(f"Failed to update address. Address with ID {_id} not found.")
            return Response({"message": "Address not found"}, status=404)

        serializer = AddressSerializer(address, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Address with ID {_id} updated successfully.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to update address with ID {_id}: {serializer.errors}")
        return Response(serializer.errors, status=401)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def delete(self, request, _id):
        try:
            address = self.get_object(request, _id)
        except Http404:
            logger.warning(f"Failed to delete address. Address with ID {_id} not found.")
            return Response({"message": "Address not found"}, status=404)

        address.is_deleted = True
        address.save()
        logger.info(f"Address with ID {_id} marked as deleted.")
        return Response({"message": "Address has been successfully removed"}, status=200)


class OrderStatusDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get_object(self, request, _id):
        return get_object_or_404(OrderStatus, id=_id)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status_name': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['status_name', 'description']
        ),
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def put(self, request, _id):
        if UserProfile.objects.get(id=get_user_id_from_token(request)).username == "bezhan" and request.data.get(
                'password') == "bezhan2009":
            try:
                order_status = self.get_object(request, _id)
            except Http404:
                logger.warning(f"Failed to update order status. Order status with ID {_id} not found.")
                return Response({"message": "Order status not found"}, status=404)

            serializer = OrderStatusSerializer(order_status, data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Order status with ID {_id} updated successfully.")
                return Response(serializer.data, status=200)
            logger.error(f"Failed to update order status with ID {_id}: {serializer.errors}")
            return Response(serializer.errors, status=401)
        return Response({"message": "You don't have permission."})


class OrderStatusList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get(self, request):
        try:
            order_statuses = OrderStatus.objects.all()
            serializer = OrderStatusSerializer(order_statuses, many=True)
            logger.info("Successfully retrieved all order statuses.")
            return Response(serializer.data, status=200)
        except Exception as e:
            logger.error(f"An error occurred while retrieving order statuses: {str(e)}")
            return Response({"error": str(e)}, status=500)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status_name': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['status_name', 'description']
        ),
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def post(self, request):
        try:
            serializer = OrderStatusSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"New order status created with ID {serializer.data.get('id')}.")
                return Response(serializer.data, status=200)
            else:
                logger.error(f"Failed to create a new order status: {serializer.errors}")
                return Response(serializer.errors, status=401)
        except Exception as e:
            logger.error(f"An error occurred while creating a new order status: {str(e)}")
            return Response({"error": str(e)}, status=500)


class AccountList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            accounts = Account.objects.filter(user=user_profile, is_deleted=False)
        except Account.DoesNotExist:
            logger.warning(f"Failed to retrieve accounts for user {user_id}. Account Not Found.")
            return Response({"message": "Account Not Found."}, status=404)
        if not accounts.exists():
            logger.warning(f"Failed to retrieve accounts for user {user_id}. Account Not Found.")
            return Response({"message": "You have any accounts."}, status=404)
        serializer = AccountSerializer(accounts, many=True)
        logger.info(f"User with ID {user_id} retrieved their accounts.")
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'account_number': openapi.Schema(type=openapi.TYPE_STRING,
                                                 description="Account number for new account"),
            },
            required=['account_number']
        ),
        security=[],
    )
    def post(self, request):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)
            serializer.save(user=user_profile)
            logger.info(f"New account created with ID {serializer.data.get('id')} for user {user_id}.")
            return Response({"message": "Account created successfully"}, status=200)
        logger.error(f"Failed to create a new account: {serializer.errors}")
        return Response(serializer.errors, status=401)


class AccountDetails(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get_object(self, request, _id):
        user_id = get_user_id_from_token(request)
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            account = get_object_or_404(Account, user=user_profile, id=_id, is_deleted=False)
            return account
        except UserProfile.DoesNotExist:
            logger.warning(f"User profile not found for user with ID {user_id}.")
            raise Http404({"message": "User profile not found"})
        except Account.DoesNotExist:
            logger.warning(f"Account not found with ID {_id} for user with ID {user_id}.")
            raise Http404({"message": "Account not found"})
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            raise Response({"error": str(e)}, status=500)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get(self, request, _id):
        try:
            account = self.get_object(request, _id)
            serializer = AccountSerializer(account, many=False)
            return Response(serializer.data, status=200)
        except Http404:
            logger.warning(f"Failed to retrieve account with ID {_id}. Account not found.")
            return Response({"message": "Account not found"}, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"message": str(e)}, status=500)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'fill': openapi.Schema(type=openapi.TYPE_NUMBER, description="Amount to fill the account balance"),
                # Add other properties as needed
            },
            required=['fill']
        ),
        security=[],
    )
    def put(self, request, _id):
        try:
            account = self.get_object(request, _id)
            serializer = AccountSerializer(account, data=request.data, partial=True)  # Use data=request.data
        except Http404:
            logger.warning(f"Failed to retrieve account with ID {_id}. Account not found.")
            return Response({"message": "Account Not Found"}, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"error": str(e)}, status=500)

        fill = request.data.get('fill')
        if not isinstance(fill, (int, float)):
            return Response({"warning": "Invalid fill value. It should be a number."}, status=401)
        elif fill < 10000:
            serializer.is_valid(raise_exception=True)  # Validate the serializer
            account.balance += fill
            account.save()
            logger.info(f"Account with ID {_id} balance updated successfully\n\tdata: {serializer.data}.")
            return Response(serializer.data, status=200)
        else:
            logger.warning(f"Failed to update account with ID {_id}. Fill value is too high.")
            return Response({"warning": "Fill value is too high. Maximum allowed is 10000."}, status=401)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def delete(self, request, _id):
        try:
            account = self.get_object(request, _id)
        except Account.DoesNotExist:
            logger.warning(f"Failed to delete account. Account with ID {_id} not found.")
            return Response({"message": "Account Not Found"}, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"message": str(e)}, status=500)

        account.is_deleted = True
        account.save()
        logger.info(f"Account with ID {_id} marked as deleted.")
        return Response({"message": "Account has been successfully removed"}, status=200)


class ReviewDetail(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get_object(self, request, _id):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)
        return get_object_or_404(Review, id=_id, is_deleted=False)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def get(self, request, _id):
        try:
            review = Review.objects.get(id=_id)
            serializer = ReviewSerializer(review, many=False)
            return Response(serializer.data, status=200)
        except Review.DoesNotExist:
            logger.warning(f"Failed to get review with ID {_id}. Review not found.")
            return Response({"message": "Review not found"}, status=404)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to get review with ID {_id}. User profile not found.")
            return Response({"message": "User profile not found"}, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"error": str(e)}, status=500)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'rating': openapi.Schema(type=openapi.TYPE_NUMBER, description="Amount to fill the account balance"),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Amount to fill the account balance"),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Amount to fill the account balance"),
            },
        ),
        security=[],
    )
    def put(self, request, _id):
        try:
            review = self.get_object(request, _id)
            serializer = ReviewSerializer(review, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                logger.info(f"Review with ID {_id} updated successfully\n\tdata: {serializer.data}.")
                return Response(serializer.data, status=200)
            else:
                logger.error(f"Failed to update review with ID {_id}: {serializer.errors}\n\tdata: {serializer.data}")
                return Response(serializer.errors, status=400)

        except Http404:
            logger.warning(f"Failed to update review with ID {_id}. Review not found.")
            return Response({"message": "Review not found"}, status=404)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to update review with ID {_id}. User profile not found.")
            return Response({"message": "User profile not found"}, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"error": str(e)}, status=500)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def delete(self, request, _id):
        try:
            review = self.get_object(request, _id)
            review.delete()
            review.save()
            logger.info(f"Review with ID {_id} marked as deleted.")
        except Http404:
            logger.warning(f"Failed to delete review with ID {_id}. Review not found.")
            return Response({"message": "Review Not Found"}, status=404)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to delete review with ID {_id}. User profile not found.")
            return Response({"message": "User Not Found"}, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"error": str(e)}, status=500)
        return Response({"message": "Review has been successfully deleted"}, status=200)


class ReviewList(APIView):
    def get(self, request, product_id):
        try:
            review = Review.objects.get(product=Product.objects.get(id=product_id), is_deleted=False)
            serializer = ReviewSerializer(review)
        except Review.DoesNotExist:
            logger.warning(f"Failed to get reviews. Review not found.")
            return Response({"message": "Review not found"}, status=404)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to get reviews. User profile not found.")
            return Response({"message": "User profile not found"}, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"error": str(e)}, status=500)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'rating': openapi.Schema(type=openapi.TYPE_NUMBER),
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'content': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['rating', 'title', 'content']
        ),
        security=[],
    )
    def post(self, request, product_id):
        try:
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)
            product = Product.objects.get(id=product_id)

            # Проверка, существует ли отзыв от данного пользователя для данного продукта
            existing_review = Review.objects.filter(product=product, user=user_profile).first()

            if existing_review:
                return Response({"message": "Review from you already exists"}, status=status.HTTP_400_BAD_REQUEST)

            serializer = ReviewSerializer(data=request.data)

            try:
                order_details = OrderDetails.objects.filter(product=product).first()
                order = Order.objects.filter(order_details=order_details, is_paid=True).first()
                if order:
                    if serializer.is_valid():
                        serializer.save(product=product, user=user_profile)
                        return Response(serializer.data, status=status.HTTP_201_CREATED)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": "Buy the item before passing judgment on it."},
                                    status=status.HTTP_401_UNAUTHORIZED)
            except OrderDetails.DoesNotExist:
                return Response({"message": "Buy the item before passing judgment on it."},
                                status=status.HTTP_401_UNAUTHORIZED)
            except Order.DoesNotExist:
                return Response({"message": "Buy the item before passing judgment on it."},
                                status=status.HTTP_401_UNAUTHORIZED)
        except UserProfile.DoesNotExist:
            return Response({"message": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Product.DoesNotExist:
            logger.warning(f"Failed to create a new comment. Product not found.")
            return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentList(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    def get_object(self, product_id):
        try:
            product = get_object_or_404(Product, id=product_id)
            comments = Comment.objects.filter(product=product)
            comments_dict = {comment.id: [] for comment in comments}

            for comment in comments:
                if comment.parent_id:
                    comments_dict[comment.parent_id].append(comment)

            main_comments = [comment for comment in comments if not comment.parent_id]

            return main_comments, comments_dict
        except Product.DoesNotExist:
            logger.warning(f"Failed to get comments. Product not found.")
            raise Response({"message": "Product not found"}, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            raise Response({"error": str(e)}, status=500)

    def get(self, request, product_id):
        try:
            main_comments, comments_dict = self.get_object(product_id)
            main_comments_tree = [build_comment_tree(comment, comments_dict) for comment in main_comments]
            return Response(main_comments_tree, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'parent_id': openapi.Schema(type=openapi.TYPE_NUMBER),
                'comment_text': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['comment_text']
        ),
        security=[],
    )
    def post(self, request, product_id):
        try:
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                parent_comment_id = request.data.get('parent_id')
                product = Product.objects.get(id=product_id)

                if parent_comment_id:
                    parent_comment = Comment.objects.get(id=parent_comment_id)
                    new_comment = serializer.save(user=user_profile,
                                                  product=product)  # Сначала сохраняем новый комментарий
                    parent_comment.children.add(
                        new_comment)  # Устанавливаем связь между родительским и дочерним комментариями
                else:
                    serializer.save(user=user_profile, product=product)

                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to create a new comment. User profile not found.")
            return Response({"message": "You have not registered yet"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, _comment_id):
        try:
            return Comment.objects.get(id=_comment_id)
        except Comment.DoesNotExist:
            logger.warning(f"Failed to get comments. Comment not found.")
            raise Http404({"message": "Comment not found"})
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            raise Response({"error": str(e)}, status=500)

    @transaction.atomic
    def delete_comment_chain(self, comment):
        # Recursively delete comment chain
        child_comments = Comment.objects.filter(parent_id=comment.id)
        for child_comment in child_comments:
            self.delete_comment_chain(child_comment)
            child_comment.delete()

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def delete(self, request, comment_id):
        try:
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)
            comment = Comment.objects.get(id=comment_id, user=user_profile)
            logger.info(f"Attempting to delete comment with ID {comment_id}.")
        except Comment.DoesNotExist:
            logger.warning(f"Failed to delete Comment. Comment with ID {comment_id} not found.")
            return Response({"message": "Comment Not Found"}, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Delete the entire comment chain
        self.delete_comment_chain(comment)

        # Delete the parent comment
        comment.delete()

        return Response(True, status=200)


class ProductUser(APIView):
    def get(self, request, user_id):
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            products = Product.objects.filter(user=user_profile)

            if not products.exists():
                return Response({"message": f"No products found for the user with id {user_id}"},
                                status=status.HTTP_404_NOT_FOUND)

            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to get user profile. User profile not found.")
            return Response({"message": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AboutUs(APIView):
    def get(self, reqeust):
        return Response({"message": f"Hello we are Aether"}, status=200)


class DetailProduct(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the category"),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Title of the item"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description of the item"),
                'price': openapi.Schema(type=openapi.TYPE_INTEGER, description="Price of the item"),
                'amount': openapi.Schema(type=openapi.TYPE_INTEGER, description="Amount of the item"),
                'default_account': openapi.Schema(type=openapi.TYPE_INTEGER, description="Default account for money")
            },
            required=['category', 'title', 'description', 'price', 'amount']
        ),
        security=[],
    )
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=UserProfile.objects.get(id=get_user_id_from_token(request)))
            return Response(True, status=201)
        return Response(serializer.errors, status=401)
