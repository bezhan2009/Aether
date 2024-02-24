
from datetime import date
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .serializers import *
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
import logging
from django.db.models import Q
from django.http import Http404

logger = logging.getLogger('django')
deposit = 15


def get_user_id_from_token(request):
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header:
            access_token = AccessToken(authorization_header.split()[1])
            user_id = access_token['user_id']
            return user_id
        else:
            return None
    except (AuthenticationFailed, IndexError):
        return None


class ProductDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, request, _id):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)
        return Product.objects.filter(user=user_profile, is_admin=True)

    def get(self, request, _id):
        try:
            product = self.get_object(request, _id)
        except Product.DoesNotExist:
            logger.error(f"Product with ID {_id} not found.")
            return Response(status=404)

        serializer = ProductSerializer(product)
        logger.info(f"User with ID {get_user_id_from_token(request)} retrieved product with ID {_id}.")
        return Response(serializer.data)

    def put(self, request, _id):
        try:
            product = self.get_object(request, _id)
        except Product.DoesNotExist:
            logger.error(f"Product with ID {_id} not found.")
            return Response(status=404)

        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)

        if not product.is_deleted and user_profile.is_admin:
            serializer = ProductSerializer(product, data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User with ID {user_id} modified product {_id} sending the following data to the server: {serializer.data}")
                return Response(serializer.data, status=200)
            else:
                logger.error(f"Invalid data received while modifying product {_id}: {serializer.errors}")
                return Response(serializer.errors, status=401)
        else:
            logger.warning(f"Attempt to modify a deleted product or unauthorized access by user with ID {user_id}.")
            return Response("Product has already been deleted or unauthorized access.", status=401)

    def delete(self, request, _id):
        try:
            product = self.get_object(request, _id)
            logger.info(f"Attempting to delete product with ID {_id}.")
        except Product.DoesNotExist:
            logger.warning(f"Failed to delete product. Product with ID {_id} not found.")
            return Response(False, status=404)

        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)

        if not product.is_deleted and user_profile.is_admin:
            product.is_deleted = True
            product.save()
            logger.info(f"Product with ID {_id} marked as deleted.")
        else:
            logger.warning(f"Failed to delete product. Product with ID {_id} has already been deleted or user is not an admin.")
            return Response("Product has already been deleted.", status=200)

        return Response(True, status=200)


class ProductList(APIView):
    def get(self, request):
        show_own_products = request.query_params.get('show_own_products', False)
        try:
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)

            if user_profile.is_admin and not show_own_products:
                products = Product.objects.all()
            elif user_profile.is_admin and show_own_products:
                products = Product.objects.filter(user=user_profile)
            else:
                products = Product.objects.all()

            search_query = request.query_params.get('search', None)
            if search_query:
                products = products.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

            products = products[:30]  # Apply slicing after filtering

            # Serialize products along with related ProductImage instances
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)

        except UserProfile.DoesNotExist:
            user_id = get_user_id_from_token(request)
            products = Product.objects.all()[:30]
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. User profile not found.")
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)

        except Product.DoesNotExist:
            user_id = get_user_id_from_token(request)
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. No products found.")
            return Response("No products found for the user", status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        try:
            # Get the array of images from the request data
            cover_imgs = request.data.get('cover_img')

            # Get the user profile based on the token or however you identify the user
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)

            # Check if the user is an admin
            if not user_profile.is_admin:
                raise PermissionDenied("You don't have permission to create a product.")

            data = {
                'user': user_profile,
                'category': request.data.get('category'),
                'title': request.data.get('title'),
                'description': request.data.get('description'),
                'price': request.data.get('price'),
                'amount': request.data.get('amount'),
            }

            # Log request data
            logger.info(f"Request data - User: {user_profile.username}, Data: {data}, Cover Images: {cover_imgs}")

            # Create a ProductSerializer instance with the data and cover_imgs
            serializer = ProductSerializer(data=data)

            if serializer.is_valid():
                # Save the product instance
                product = serializer.save()

                # Save each image in the cover_imgs array
                for cover_img in cover_imgs:
                    ProductImage.objects.create(product=product, image=cover_img)

                # Log information including user details, product ID, and image details
                logger.info(f"Product created successfully. User: {user_profile.username}, Product ID: {product.id}, Cover Images: {cover_imgs}")

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Invalid data provided: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as pd:
            logger.warning(f"Permission Denied: {str(pd)}")
            return Response(str(pd), status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return Response("An error occurred", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, request, _id):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(user_id=user_id)
        return get_object_or_404(OrderDetails, id=_id, user=user_profile, is_admin=False)

    def get(self, request, _id):
        try:
            orders = self.get_object(request, _id)
            logger.info(f"Order details retrieved successfully for user with ID {get_user_id_from_token(request)}.")
        except UserProfile.DoesNotExist:
            user_id = get_user_id_from_token(request)
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. User profile not found.")
            return Response("You have not registered yet", status=status.HTTP_404_NOT_FOUND)
        except OrderDetails.DoesNotExist:
            logger.warning(f"Failed to retrieve order details for user with ID {get_user_id_from_token(request)}.")
            return Response("You have not registered yet", status=404)

        serializer = OrderDetailsSerializer(orders, many=True)
        return Response(serializer.data, status=200)

    def put(self, request, _id):
        try:
            product = self.get_object(request, _id)
            logger.info(f"Attempting to update order detail with ID {_id}.")
        except UserProfile.DoesNotExist:
            user_id = get_user_id_from_token(request)
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. User profile not found.")
            return Response("You have not registered yet", status=status.HTTP_404_NOT_FOUND)
        except Product.DoesNotExist:
            logger.warning(f"Failed to update order detail. Order detail with ID {_id} not found.")
            return Response(status=404)

        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Order detail with ID {_id} updated successfully.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to update order detail with ID {_id}: {serializer.errors}")
        return Response(serializer.errors, status=401)

    def delete(self, request, _id):
        try:
            product = self.get_object(request, _id)
        except UserProfile.DoesNotExist:
            user_id = get_user_id_from_token(request)
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. User profile not found.")
            return Response("You have not registered yet", status=status.HTTP_404_NOT_FOUND)
        except OrderDetails.DoesNotExist:
            logger.warning(f"Failed to delete order detail. Order detail with ID {_id} not found.")
            return Response(False, status=status.HTTP_404_NOT_FOUND)

        product.is_deleted = True
        product.save()

        logger.info(f"Order detail with ID {_id} marked as deleted.")
        return Response(True, status=status.HTTP_200_OK)


class OrderPay(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_order(self, _id):
        return get_object_or_404(Order, id=_id, is_paid=False)

    def post(self, request, _id):
        try:
            order = self.get_order(_id)
            logger.info(f"Attempting to process payment for order with ID {_id}.")
        except Order.DoesNotExist:
            logger.warning(f"Failed to process payment. Order with ID {_id} not found.")
            return Response(False, status=404)

        try:
            order_details = OrderDetails.objects.get(id=order.order_details.id)
        except OrderDetails.DoesNotExist:
            logger.warning(f"Failed to process payment. Order details not found for order with ID {_id}.")
            return Response(False, status=404)

        _account_number = request.data.get('account_number')

        try:
            account = Account.objects.get(account_number=_account_number)
        except Account.DoesNotExist:
            logger.warning(f"Failed to process payment. Account not found for account number {_account_number}.")
            return Response(False, status=404)

        try:
            user_profile = UserProfile.objects.get(id=order.user.id)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to process payment. User profile not found for user with ID {order.user.id}.")
            return Response(False, status=404)

        if account.balance > 0 and account.balance > order_details.price:
            account.balance -= order_details.price
            product = Product.objects.get(id=order_details.product.id)
            user_product = UserProfile.objects.get(id=product.user.id)
            account_user_product = Account.objects.filter(user=user_product).first()
            account_user_product.balance += order_details.price
            order.is_paid = True
            order.is_in_the_card = False
            order.status = 3
        else:
            logger.warning(f"Failed to process payment. Insufficient funds for order with ID {_id}.")
            return Response("You do not have enough funds to make the purchase", status=401)

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
        account_user_product.save()

        logger.info(f"Payment processed successfully for order with ID {_id}.")
        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=200)


class OrderPaid(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id, is_admin=False)
        orders = Order.objects.filter(is_paid=True)
        product = Product.objects.filter(id=orders.product.id, user=user_profile)
        if product:
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=200)
        else:
            return Response(False, status=404)


class PayMentDetail(APIView):
    def get(self, request, _id):
        try:
            payment = Payment.objects.get(id=_id)
            logger.info(f"Payment details retrieved successfully for payment with ID {_id}.")
        except Payment.DoesNotExist:
            logger.warning(f"Failed to retrieve payment details. Payment with ID {_id} not found.")
            return Response(False, status=status.HTTP_404_NOT_FOUND)

        serializer = PaymentSerializer(payment, many=False)
        return Response(serializer.data, status=200)

    def delete(self, request, _id):
        try:
            payment = Payment.objects.get(id=_id)
        except Payment.DoesNotExist:
            logger.warning(f"Failed to delete payment. Payment with ID {_id} not found.")
            return Response(False, status=status.HTTP_404_NOT_FOUND)

        if not payment.is_deleted:
            payment.is_deleted = True
            payment.save()
            logger.info(f"Payment with ID {_id} marked as deleted.")
        else:
            logger.warning(f"Failed to delete payment. Payment with ID {_id} has already been deleted.")

        serializer = PaymentSerializer(payment, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id, is_admin=False)
        try:
            orders = Order.objects.prefetch_related(
                'status',
                'order_details__product',
                'order_details__address'
            ).filter(user=user_profile)
        except UserProfile.DoesNotExist:
            user_id = get_user_id_from_token(request)
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. User profile not found.")
            return Response("You have not registered yet", status=status.HTTP_404_NOT_FOUND)
        except Order.DoesNotExist:
            logger.warning(f"User with ID {user_id} has not registered yet.")
            return Response("You are not registered yet", status=404)

        # Сериализация данных
        serializer = OrderSerializer(orders, many=True)
        logger.info(f"User with ID {user_id} retrieved their orders.")
        return Response(serializer.data, status=200)

    def post(self, request):
        serializer = OrderDetailsNewSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product'].id
            try:
                product = Product.objects.get(id=product_id)
            except UserProfile.DoesNotExist:
                user_id = get_user_id_from_token(request)
                logger.warning(f"Failed to retrieve products for user with ID {user_id}. User profile not found.")
                return Response("You have not registered yet", status=status.HTTP_404_NOT_FOUND)
            except Product.DoesNotExist:
                logger.error(f"Product with ID {product_id} not found.")
                return Response(status=404)

            address_id = serializer.validated_data['address']
            amount = serializer.validated_data['quantity']

            if amount > product.amount:
                logger.warning(f"Insufficient stock for product with ID {product_id}.")
                return Response(False, status=401)
            else:
                product.amount -= amount
                product.save()
                if not product.amount:
                    product.is_deleted = True
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)

            order_details = OrderDetails.objects.create(
                user=user_profile,
                product=product,
                price=product.price,
                quantity=amount,
                address=address_id
            )

            # Получаем объект OrderStatus по его id или любым другим способом
            order_status = OrderStatus.objects.get(id=1)

            order = Order.objects.create(
                status=order_status,
                order_details=order_details
            )

            logger.info(f"User with ID {user_id} placed a new order with ID {order.id}.")
            return Response(True, status=200)

        logger.error(f"Invalid data received while creating a new order: {serializer.errors}")
        return Response(serializer.errors, status=401)


class UserProfileDetails(APIView):
    def get_user(self, _id):
        return get_object_or_404(UserProfile, id=_id)

    def get(self, request, _id):
        try:
            user = self.get_user(_id)
            logger.info(f"User with ID {_id} retrieved successfully.")
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to retrieve user. User with ID {_id} not found.")
            return Response(False, status=404)

        serializer = UserProfileSerializer(user, many=False)
        return Response(serializer.data, status=200)

    def put(self, request, _id):
        try:
            user = self.get_user(_id)
            logger.info(f"Attempting to update user with ID {_id}.")
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to update user. User with ID {_id} not found.")
            return Response(status=404)

        serializer = UserProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User with ID {_id} updated successfully.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to update user with ID {_id}: {serializer.errors}")
        return Response(serializer.errors, status=401)


@api_view(['GET'])
def get_user_all(request):
    try:
        users = UserProfile.objects.all()
        logger.info("All users retrieved successfully.")
    except Product.DoesNotExist:
        logger.warning("Failed to retrieve all users.")
        return Response("You have not registered yet")

    serializer = UserProfileSerializer(users, many=True)
    return Response(serializer.data, status=200)


@api_view(["POST"])
def create_user(request):
    serializer = UserProfileSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        serializer = UserProfileSerializer(user)
        logger.info(f"New user created with ID {user.id}.")
        return Response(serializer.data)
    logger.error(f"Failed to create a new user: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAuthorization(APIView):
    def post(self, request):
        try:
            userProfile = UserProfile.objects.get(password=request.data.get('password'), name=request.data.get('name'),
                                                  email=request.data.get('email'))
            logger.info(f"User with ID {userProfile.id} authorized successfully.")
        except UserProfile.DoesNotExist:
            logger.warning("User authorization failed. User not found.")
            return Response(False, status=404)

        serializer = UserProfileSerializer(userProfile)
        return Response(serializer.data, status=200)


class CategoryList(APIView):
    def get(self, request):
        category = Category.objects.all()
        serializer = CategorySerializer(category, many=True)
        return Response(serializer.data, status=200)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"New category created with ID {serializer.data.get('id')}.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to create a new category: {serializer.errors}")
        return Response(False, status=401)


class CategoryDetails(APIView):
    def get_object(self, _id):
        return get_object_or_404(Category, id=_id)

    def get(self, request, _id):
        category = self.get_object(_id)
        if category:
            serializer = CategorySerializer(category, many=False)
            return Response(serializer.data, status=200)
        else:
            return get_object_or_404(Category, id=_id)

    def put(self, request, _id):
        try:
            category = self.get_object(_id)
        except Category.DoesNotExist:
            logger.warning(f"Failed to update category. Category with ID {_id} not found.")
            return Response(status=404)

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
            return Response(False, status=404)

        category.is_deleted = True
        logger.info(f"Category with ID {_id} marked as deleted.")
        return Response(True, status=200)


class AddressList(APIView):
    def get(self, request):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)
        return get_object_or_404(Address, user=user_profile)

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
    permission_classes = [IsAuthenticated]

    def get_object(self, request, _id):
        user_id = get_user_id_from_token(request)
        return get_object_or_404(Address, id=_id)

    def get(self, request, _id):
        try:
            address = self.get_object(request, _id)
            serializer = AddressSerializer(address, many=False)
            return Response(serializer.data, status=200)
        except Address.DoesNotExist:
            logger.warning(f"Failed to retrieve address. Address with ID {_id} not found.")
            return Response("Address not found", status=404)

    def put(self, request, _id):
        try:
            address = self.get_object(request, _id)
        except Address.DoesNotExist:
            logger.warning(f"Failed to update address. Address with ID {_id} not found.")
            return Response("Address not found", status=404)

        serializer = AddressSerializer(address, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Address with ID {_id} updated successfully.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to update address with ID {_id}: {serializer.errors}")
        return Response(serializer.errors, status=401)

    def delete(self, request, _id):
        try:
            address = self.get_object(request, _id)
        except Address.DoesNotExist:
            logger.warning(f"Failed to delete address. Address with ID {_id} not found.")
            return Response(False, status=404)

        address.is_deleted = True
        logger.info(f"Address with ID {_id} marked as deleted.")
        return Response(True, status=200)


class OrderStatusDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, request, _id):
        return get_object_or_404(OrderStatus, id=_id)

    def put(self, request, _id):
        try:
            order_status = self.get_object(request, _id)
        except OrderStatus.DoesNotExist:
            logger.warning(f"Failed to update order status. Order status with ID {_id} not found.")
            return Response("Order status not found", status=404)

        serializer = OrderStatusSerializer(order_status, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Order status with ID {_id} updated successfully.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to update order status with ID {_id}: {serializer.errors}")
        return Response(serializer.errors, status=401)


class OrderStatusList(APIView):
    def get(self, request):
        try:
            order_statuses = OrderStatus.objects.all()
            serializer = OrderStatusSerializer(order_statuses, many=True)
            logger.info("Successfully retrieved all order statuses.")
            return Response(serializer.data, status=200)
        except Exception as e:
            logger.error(f"An error occurred while retrieving order statuses: {str(e)}")
            return Response("Internal server error", status=500)

    def post(self, request):
        try:
            serializer = OrderStatusSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"New order status created with ID {serializer.data.get('id')}.")
                return Response(serializer.data, status=200)
            else:
                logger.error(f"Failed to create a new order status: {serializer.errors}")
                return Response("Failed to create a new order status", status=401)
        except Exception as e:
            logger.error(f"An error occurred while creating a new order status: {str(e)}")
            return Response("Internal server error", status=500)


class AccountList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            accounts = Account.objects.filter(user=user_profile, is_deleted=False)
        except Account.DoesNotExist:
            logger.warning(f"Failed to retrieve accounts for user {user_id}. User not registered.")
            return Response("You have not registered yet", status=404)
        serializer = AccountSerializer(accounts, many=True)
        logger.info(f"User with ID {user_id} retrieved their accounts.")
        return Response(serializer.data, status=200)

    def post(self, request):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)
            serializer.save(user=user_profile)
            logger.info(f"New account created with ID {serializer.data.get('id')} for user {user_id}.")
            return Response(True, status=200)
        logger.error(f"Failed to create a new account: {serializer.errors}")
        return Response("Failed to create a new account", status=401)


class AccountDetails(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, request, _id):
        user_id = get_user_id_from_token(request)
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            account = get_object_or_404(Account, user=user_profile, id=_id, is_deleted=False)
            return account
        except UserProfile.DoesNotExist:
            logger.warning(f"User profile not found for user with ID {user_id}.")
            raise Http404("User profile not found")
        except Account.DoesNotExist:
            logger.warning(f"Account not found with ID {_id} for user with ID {user_id}.")
            raise Http404("Account not found")
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            raise Http404("Account not found")

    def get(self, request, _id):
        try:
            account = self.get_object(request, _id)
            serializer = AccountSerializer(account, many=False)
            return Response(serializer.data, status=200)
        except Http404:
            logger.warning(f"Failed to retrieve account with ID {_id}. Account not found.")
            return Response("Account not found", status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=500)

    def put(self, request, _id):
        try:
            account = self.get_object(request, _id)
            serializer = AccountSerializer(account, data=request.data, partial=True)  # Use data=request.data
        except Http404:
            logger.warning(f"Failed to retrieve account with ID {_id}. Account not found.")
            return Response("Account not found", status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=500)

        fill = request.data.get('fill')
        if not isinstance(fill, (int, float)):
            return Response("Invalid fill value. It should be a number.", status=401)
        elif fill < 10000:
            serializer.is_valid(raise_exception=True)  # Validate the serializer
            account.balance += fill
            account.save()
            logger.info(f"Account with ID {_id} balance updated successfully\n\tdata: {serializer.data}.")
            return Response(serializer.data, status=200)
        else:
            logger.warning(f"Failed to update account with ID {_id}. Fill value is too high.")
            return Response("Fill value is too high. Maximum allowed is 10000.", status=401)

    def delete(self, request, _id):
        try:
            account = self.get_object(request, _id)
        except Account.DoesNotExist:
            logger.warning(f"Failed to delete account. Account with ID {_id} not found.")
            return Response(False, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=500)

        account.is_deleted = True
        account.save()
        logger.info(f"Account with ID {_id} marked as deleted.")
        return Response(True, status=200)


class ReviewDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, request, _id):
        user_id = get_user_id_from_token(request)
        user_profile = UserProfile.objects.get(id=user_id)
        return get_object_or_404(Review, id=_id, user=user_profile)

    def get(self, request, _id):
        try:
            review = self.get_object(request, _id)
            serializer = ReviewSerializer(review, many=False)
            return Response(serializer.data, status=200)
        except Http404:
            logger.warning(f"Failed to get review with ID {_id}. Review not found.")
            return Response("Review not found", status=404)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to get review with ID {_id}. User profile not found.")
            return Response("User profile not found", status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=500)

    def put(self, request, _id):
        try:
            review = self.get_object(request, _id)
            serializer = ReviewSerializer(review, data=request.data)

            if serializer.is_valid():
                serializer.save()
                logger.info(f"Review with ID {_id} updated successfully\n\tdata: {serializer.data}.")
                return Response(serializer.data, status=200)
            else:
                logger.error(f"Failed to update review with ID {_id}: {serializer.errors}\n\tdata: {serializer.data}")
                return Response(serializer.errors, status=400)

        except Http404:
            logger.warning(f"Failed to update review with ID {_id}. Review not found.")
            return Response("Review not found", status=404)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to update review with ID {_id}. User profile not found.")
            return Response("User profile not found", status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=500)

    def delete(self, request, _id):
        try:
            review = self.get_object(request, _id)
            review.is_deleted = True
            logger.info(f"Review with ID {_id} marked as deleted.")
            return Response(True, status=200)

        except Http404:
            logger.warning(f"Failed to delete review with ID {_id}. Review not found.")
            return Response(False, status=404)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to delete review with ID {_id}. User profile not found.")
            return Response(False, status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=500)


class ReviewList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = get_user_id_from_token(request)
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            return get_object_or_404(Review, user=user_profile)
        except UserProfile.DoesNotExist:
            logger.warning(f"Failed to get reviews. User profile not found.")
            return Response("User profile not found", status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=500)

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)

        if serializer.is_valid():
            user_id = get_user_id_from_token(request)
            try:
                user_profile = UserProfile.objects.get(id=user_id)
                serializer.save(user=user_profile)
                logger.info(f"New review created with ID {serializer.data.get('id')} for user {user_id}.")
                return Response(serializer.data, status=200)
            except UserProfile.DoesNotExist:
                logger.warning(f"Failed to create a new review. User profile not found.")
                return Response("User profile not found", status=404)
            except Exception as e:
                logger.error(f"An error occurred while processing the request: {str(e)}")
                return Response("Internal server error", status=500)
        else:
            logger.error(f"Failed to create a new review: {serializer.errors}")
            return Response(serializer.errors, status=400)


class CommentList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, product_id):
        try:
            product = get_object_or_404(Product, id=product_id)
            return Comment.objects.filter(product=product)
        except Product.DoesNotExist:
            logger.warning(f"Failed to get comments. Product not found.")
            return Response("Product not found", status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            logger.warning(f"Failed to get comments. Comment not found.")
            return Response("Comment not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, product_id):
        try:
            comments = self.get_object(product_id)
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Response as response:
            return response
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            user_id = get_user_id_from_token(request)
            user_profile = UserProfile.objects.get(id=user_id)
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user_profile)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentDetail(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, _comment_id):
        try:
            return Comment.objects.filter(id=_comment_id)
        except Comment.DoesNotExist:
            logger.warning(f"Failed to get comments. Comment not found.")
            return Response("Comment not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, comment_id):
        try:
            comment = self.get_object(comment_id)
            logger.info(f"Attempting to update order detail with ID {comment_id}.")
        except UserProfile.DoesNotExist:
            user_id = get_user_id_from_token(request)
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. User profile not found.")
            return Response("You have not registered yet", status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            logger.warning(f"Failed to update Comment. Comment with ID {comment_id} not found.")
            return Response(status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer = ProductSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Comment with ID {comment_id} updated successfully.")
            return Response(serializer.data, status=200)
        logger.error(f"Failed to update Comment with ID {comment_id}: {serializer.errors}")
        return Response(serializer.errors, status=401)

    def delete(self, request, comment_id):
        try:
            comment = self.get_object(comment_id)
            logger.info(f"Attempting to delete order detail with ID {comment_id}.")
        except UserProfile.DoesNotExist:
            user_id = get_user_id_from_token(request)
            logger.warning(f"Failed to retrieve products for user with ID {user_id}. User profile not found.")
            return Response("You have not registered yet", status=status.HTTP_404_NOT_FOUND)
        except Comment.DoesNotExist:
            logger.warning(f"Failed to delete Comment. Comment with ID {comment_id} not found.")
            return Response(status=404)
        except Exception as e:
            logger.error(f"An error occurred while processing the request: {str(e)}")
            return Response("Internal server error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        comment.delete()
        return Response(status=204)



