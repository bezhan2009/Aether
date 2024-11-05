from django.shortcuts import get_object_or_404
from rest_framework import permissions
from drf_yasg import openapi
from django.db import transaction
from .serializers import *
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from utils.tokens import get_user_id_from_token
from orderapp.models import (Order,
                             OrderDetails,
                             OrderStatus
                             )
from payapp.models import Account
from productapp.models import Product


logger = logging.getLogger('payapp.views')


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
        account = None
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

