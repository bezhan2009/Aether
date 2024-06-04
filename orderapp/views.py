from django.shortcuts import get_object_or_404
from rest_framework import permissions
from drf_yasg import openapi
from django.db import transaction
from .serializers import *
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from utils.tokens import get_user_id_from_token
from userapp.models import UserProfile


logger = logging.getLogger('orderapp.views')


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

