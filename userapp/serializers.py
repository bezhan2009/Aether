from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from userapp.models import *


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'password', 'age', 'is_admin']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        name = validated_data.get('username', None)
        if UserProfile.objects.filter(username=name).exists():
            self.errors['username'] = ['The username is already taken.']
            raise serializers.ValidationError('The username is already taken. ')

        user_password = validated_data.get('password', None)
        hashed_password = make_password(user_password)
        validated_data['password'] = hashed_password

        return super(UserProfileSerializer, self).create(validated_data)
