from rest_framework import serializers
from .models import User, AdminUser, CustomerUser, CustomerProfile

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ['shipping_address', 'billing_address', 'loyalty_points', 'tier']


class UserSerializer(serializers.ModelSerializer):
    profile = CustomerProfileSerializer(source='customer_profile', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'avatar', 'role', 'is_verified', 'created_at', 'profile']
        read_only_fields = ['id', 'created_at']


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = CustomerUser
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'phone']

    def create(self, validated_data):
        user = CustomerUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', '').strip(),
            last_name=validated_data.get('last_name', '').strip(),
            phone=validated_data.get('phone', ''),
            role=User.ROLE_CUSTOMER,
        )
        return user


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = AdminUser
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'phone', 'role', 'is_staff']

    def create(self, validated_data):
        user = AdminUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', '').strip(),
            last_name=validated_data.get('last_name', '').strip(),
            phone=validated_data.get('phone', ''),
            role=User.ROLE_ADMIN,
            is_staff=True,
        )
        return user
