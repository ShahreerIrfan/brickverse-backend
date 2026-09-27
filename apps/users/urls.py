from django.urls import path
from .views import (
     RegisterCustomerView,
     LoginView,
     LogoutView,
     CurrentUserProfileView,
     CustomerListView,
     AdminUserListView,
     AllUsersListView,
     UserDetailUpdateView,
     ChangePasswordView,
     SendSignupOTPView,
     VerifySignupOTPView,
     ResendOTPView,
 )

urlpatterns = [
    path('register/', RegisterCustomerView.as_view(), name='customer-register'),
    path('send-otp/', SendSignupOTPView.as_view(), name='send-signup-otp'),
    path('verify-otp-register/', VerifySignupOTPView.as_view(), name='verify-signup-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('logout/', LogoutView.as_view(), name='user-logout'),
    path('me/', CurrentUserProfileView.as_view(), name='user-profile'),
    path('all/', AllUsersListView.as_view(), name='all-users-list'),
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('admins/', AdminUserListView.as_view(), name='admin-list'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('<int:id>/', UserDetailUpdateView.as_view(), name='user-detail-update'),
]


