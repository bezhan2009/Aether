from django.shortcuts import get_object_or_404
from rest_framework import permissions
from drf_yasg import openapi
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from utils.tokens import get_user_id_from_token
from .models import (UserProfile,
                     Account
                     )
from .serializers import AccountSerializer


logger = logging.getLogger('accountapp.views')


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
            return Response({"message": "You have not any accounts."}, status=404)
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
            return Response({"error": str(e)}, status=500)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'fill': openapi.Schema(type=openapi.TYPE_NUMBER, description="Amount to fill the account balance"),
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
            return Response({"error": str(e)}, status=500)

        account.is_deleted = True
        account.save()
        logger.info(f"Account with ID {_id} marked as deleted.")
        return Response({"message": "Account has been successfully removed."}, status=200)
