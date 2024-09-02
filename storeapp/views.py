from utils.tokens import get_user_id_from_token
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from drf_yasg import openapi
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger('storeapp.views')


class StoreList(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'description': openapi.Schema(type=openapi.TYPE_STRING),
            'hash_password': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ))
    def post(self, request):
        data = {
            'name': request.data['username'],
            'description': request.data['description'],
            'hash_password': request.data['password'],
        }
        serializer = StoreSerializer(data=data)
        if serializer.is_valid():
            user = UserProfile.objects.create_user(**data)
            refresh = RefreshToken.for_user(user)
            logger.info(f"New user created with ID {user.id}.")
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StoreDetails(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_user(self, _id):
        return get_object_or_404(Store, id=_id)

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
        except Store.DoesNotExist:
            logger.warning(f"Failed to retrieve user. User with ID {user_id} not found.")
            return Response({"error": "User Not Found"}, status=404)

        serializer = StoreSerializer(user, many=False)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['username']
        ),
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def put(self, request):
        store_id = get_user_id_from_token(request)
        try:
            store = self.get_user(store_id)
            logger.info(f"Attempting to update store with ID {store_id}.")
        except Store.DoesNotExist:
            logger.warning(f"Failed to update store. User with ID {store_id} not found.")
            return Response({"error": "User Not Found."}, status=404)

        serializer = StoreSerializer(store, data=request.data, partial=True)
        if 'hash_password' in request.data:
            return Response({"error": "Changing password is not allowed."}, status=403)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User with ID {store_id} updated successfully.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to update store with ID {store_id}: {serializer.errors}")
        return Response(serializer.errors, status=401)
