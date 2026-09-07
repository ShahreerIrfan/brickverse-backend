from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from .models import User, CustomerUser, AdminUser
from .serializers import (
    UserSerializer,
    CustomerRegistrationSerializer,
    AdminUserSerializer,
)

class RegisterCustomerView(generics.CreateAPIView):
    queryset = CustomerUser.objects.all()
    serializer_class = CustomerRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend='apps.users.backends.EmailAuthBackend')
        return Response({
            "message": "Account created successfully! Welcome to Brickverse.",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {"error": "Please provide both email and password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response(
                {"error": "Invalid email or password. Please try again."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        login(request, user, backend='apps.users.backends.EmailAuthBackend')
        return Response({
            "message": f"Welcome back, {user.first_name or user.email}!",
            "user": UserSerializer(user).data
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


class CurrentUserProfileView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                "authenticated": True,
                "user": UserSerializer(request.user).data
            })
        return Response({"authenticated": False, "user": None})


class CustomerListView(generics.ListAPIView):
    queryset = CustomerUser.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    pagination_class = None


class AdminUserListView(generics.ListAPIView):
    queryset = AdminUser.objects.all().order_by('-created_at')
    serializer_class = AdminUserSerializer
    pagination_class = None


class AllUsersListView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = User.objects.all().order_by('-created_at')
        role = self.request.query_params.get('role')
        search = self.request.query_params.get('search')
        if role and role.lower() != 'all':
            queryset = queryset.filter(role=role.lower())
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        password = self.request.data.get('password', 'User1234!')
        user = serializer.save()
        user.set_password(password)
        user.save()


class UserDetailUpdateView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'

    def perform_update(self, serializer):
        role = self.request.data.get('role')
        user = serializer.save()
        if role:
            user.role = role
            user.is_staff = (role == User.ROLE_ADMIN)
            user.save()

