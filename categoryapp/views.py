from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from .serializers import *
import logging
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from productapp.serializers import CategorySerializer


logger = logging.getLogger('categoryapp.views')


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
