from django.shortcuts import get_object_or_404
from rest_framework import permissions
from drf_yasg import openapi
import logging
from .serializers import *
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from utils.tokens import get_user_id_from_token


logger = logging.getLogger('addressapp.views')


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
            return Response(
                            data={"message": "Address not found"},
                            status=404
                        )

        address.is_deleted = True
        address.save()
        logger.info(f"Address with ID {_id} marked as deleted.")
        return Response({"message": "Address has been successfully removed"}, status=200)
