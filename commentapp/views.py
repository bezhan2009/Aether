from django.shortcuts import get_object_or_404
from rest_framework import permissions
from drf_yasg import openapi
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
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
from utils.commentTree import build_comment_tree

logger = logging.getLogger('commentapp.views')


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
