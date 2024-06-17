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
        user_id = get_user_id_from_token(request)
        user = UserProfile.objects.get(id=user_id)
        featured_products = FeaturedProduct.objects.filter(user=user, is_deleted=False)
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

            featured_product = FeaturedProduct.objects.filter(product=product, user=user).first()
            if featured_product:
                if featured_product.is_deleted:
                    featured_product.is_deleted = False
                    featured_product.save()
                    return Response(data={"message": "We successfully added product to features."},
                                    status=status.HTTP_201_CREATED)
                else:
                    return Response(data={"message": "You have already added this product to your favorites."},
                                    status=status.HTTP_200_OK)
            else:
                FeaturedProduct.objects.create(product=product, user=user)
                return Response(data={"message": "We successfully added product to features."},
                                status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("Internal server error when creating a Featured Product: %s", str(e))
            return Response(data={"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeaturedProductDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('Authorization', openapi.IN_HEADER, description="Bearer <token>",
                              type=openapi.TYPE_STRING),
        ],
        security=[],
    )
    def delete(self, request, pk):
        user_id = get_user_id_from_token(request)
        user = UserProfile.objects.get(id=user_id)
        try:
            featured_product = FeaturedProduct.objects.get(id=pk, user=user, is_deleted=False)
        except FeaturedProduct.DoesNotExist:
            return Response(data={"message": "Featured Product does not exist."},
                            status=status.HTTP_404_NOT_FOUND)

        featured_product.is_deleted = True
        featured_product.save()
        return Response(data={"message": "product has been successfully removed from featured products"},
                        status=status.HTTP_200_OK)

