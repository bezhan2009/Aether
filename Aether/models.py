from django.db import models
from django.contrib.auth.models import User
from userapp.models import UserProfile
from productapp.models import (
    Product,
    Account,
    Category
)
from orderapp.models import (OrderStatus,
                             OrderDetails,
                             Payment,
                             Address
                             )
from categoryapp.models import Category
from commentapp.models import Comment
