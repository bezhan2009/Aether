from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from .serializers import *
import logging
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from utils.tokens import get_user_id_from_token

from orderapp.models import (Order,
                             OrderDetails
                             )

logger = logging.getLogger('reviewapp.views')


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
