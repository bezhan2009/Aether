from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import permissions
from drf_yasg import openapi

import logging

from featured_productapp.models import FeaturedProduct
from featured_productapp.serializers import FeaturesProductSerializer
from productapp.models import Product
from drf_yasg.utils import swagger_auto_schema
from utils.tokens import get_user_id_from_token
from userapp.models import UserProfile


logger = logging.getLogger('featured_productapp.views')


class FeaturedProductsList(APIView):
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
        featured_products = FeaturedProduct.objects.all()
        serializer = FeaturesProductSerializer(featured_products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'product': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['product']
        ),
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def post(self, request):
        try:
            product_id = request.data.get("product")
            user_id = get_user_id_from_token(request)

            try:
                user = UserProfile.objects.get(id=user_id)
            except UserProfile.DoesNotExist:
                return Response(data={"message": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response(data={"message": "Product does not exist."}, status=status.HTTP_404_NOT_FOUND)

            featured_product = FeaturedProduct.objects.filter(product=product, user=user)
            if len(featured_product):
                return Response(data={"message": "You have already added this product to your favorites."}, status=status.HTTP_200_OK)

            featured_product = FeaturedProduct.objects.create(product=product, user=user)
            featured_product.save()

            return Response(data={"message": "We successfully added product to features."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("internal server error when func FeaturedProductsList.post creating a Featured Product error: ", str(e))
            return Response(data={"error": "internal server error."})
