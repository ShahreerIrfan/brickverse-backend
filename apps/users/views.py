from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from datetime import timedelta
from django.utils import timezone
from .models import User, CustomerUser, AdminUser, EmailOTP
from .serializers import (
    UserSerializer,
    CustomerRegistrationSerializer,
    AdminUserSerializer,
)
from .utils import generate_otp_code, send_otp_email


class SendSignupOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response(
                {"error": "Please provide a valid email address."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already exists
        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"error": "An account with this email address already exists. Please log in instead."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rate limiting: Check if an OTP was sent in the last 60 seconds
        recent_otp = EmailOTP.objects.filter(
            email=email,
            purpose=EmailOTP.PURPOSE_SIGNUP,
            created_at__gte=timezone.now() - timedelta(seconds=60)
        ).first()

        if recent_otp:
            return Response(
                {"error": "Please wait a minute before requesting another OTP."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        otp_code = generate_otp_code()
        expires_at = timezone.now() + timedelta(minutes=10)

        # Invalidate previous unused signup OTPs for this email
        EmailOTP.objects.filter(
            email=email,
            purpose=EmailOTP.PURPOSE_SIGNUP,
            is_used=False
        ).update(is_used=True)

        EmailOTP.objects.create(
            email=email,
            otp=otp_code,
            purpose=EmailOTP.PURPOSE_SIGNUP,
            expires_at=expires_at
        )

        try:
            send_otp_email(to_email=email, otp_code=otp_code, purpose="signup")
        except Exception as e:
            return Response(
                {"error": f"Failed to send email OTP. Please verify your email or try again later. ({str(e)})"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "success": True,
            "message": f"A 6-digit verification code has been sent to {email}."
        }, status=status.HTTP_200_OK)


class VerifySignupOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        otp = request.data.get('otp', '').strip()
        password = request.data.get('password', '').strip()
        first_name = request.data.get('first_name', '').strip()
        last_name = request.data.get('last_name', '').strip()
        phone = request.data.get('phone', '').strip()

        if not email or not otp:
            return Response(
                {"error": "Email and 6-digit OTP are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not password or len(password) < 6:
            return Response(
                {"error": "Password must be at least 6 characters long."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"error": "An account with this email address already exists. Please log in."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify OTP
        otp_obj = EmailOTP.objects.filter(
            email=email,
            otp=otp,
            purpose=EmailOTP.PURPOSE_SIGNUP,
            is_used=False
        ).first()

        if not otp_obj:
            return Response(
                {"error": "Invalid verification code. Please check and try again."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp_obj.is_expired:
            return Response(
                {"error": "Verification code has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark OTP as used
        otp_obj.is_used = True
        otp_obj.save(update_fields=['is_used'])

        # Create Customer User
        user = CustomerUser.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_verified=True
        )

        # Auto login
        login(request, user, backend='apps.users.backends.EmailAuthBackend')

        return Response({
            "success": True,
            "message": "Account created and verified successfully! Welcome to Kawaii Subete.",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        purpose = request.data.get('purpose', EmailOTP.PURPOSE_SIGNUP)

        if not email:
            return Response(
                {"error": "Please provide your email address."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rate limiting: 60s
        recent_otp = EmailOTP.objects.filter(
            email=email,
            purpose=purpose,
            created_at__gte=timezone.now() - timedelta(seconds=60)
        ).first()

        if recent_otp:
            return Response(
                {"error": "Please wait 60 seconds before requesting a new code."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        otp_code = generate_otp_code()
        expires_at = timezone.now() + timedelta(minutes=10)

        EmailOTP.objects.filter(
            email=email,
            purpose=purpose,
            is_used=False
        ).update(is_used=True)

        EmailOTP.objects.create(
            email=email,
            otp=otp_code,
            purpose=purpose,
            expires_at=expires_at
        )

        try:
            send_otp_email(to_email=email, otp_code=otp_code, purpose=purpose)
        except Exception as e:
            return Response(
                {"error": f"Failed to send email. ({str(e)})"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "success": True,
            "message": f"A new verification code has been sent to {email}."
        }, status=status.HTTP_200_OK)


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
            "message": "Account created successfully! Welcome to Kawaii Subete.",
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
        password = self.request.data.get('password')
        user = serializer.save()
        if role:
            user.role = role
            user.is_staff = (role == User.ROLE_ADMIN)
            user.save(update_fields=['role', 'is_staff'])
        if password and str(password).strip():
            user.set_password(str(password).strip())
            user.save()


class ChangePasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        current_password = request.data.get('current_password', '')
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')
        user_id = request.data.get('user_id')
        email = request.data.get('email')

        user = None
        if request.user and request.user.is_authenticated:
            user = request.user
        elif user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass
        elif email:
            try:
                user = User.objects.get(email__iexact=email.strip())
            except User.DoesNotExist:
                pass

        if not user:
            return Response({"error": "User account not identified. Please log in first."}, status=status.HTTP_401_UNAUTHORIZED)

        if not current_password:
            return Response({"error": "Current password is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        if not new_password or len(str(new_password).strip()) < 6:
            return Response({"error": "New password must be at least 6 characters long."}, status=status.HTTP_400_BAD_REQUEST)

        if confirm_password and str(new_password).strip() != str(confirm_password).strip():
            return Response({"error": "New password confirmation does not match."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(str(new_password).strip())
        user.save()
        return Response({"success": True, "message": "Password updated successfully!"}, status=status.HTTP_200_OK)


