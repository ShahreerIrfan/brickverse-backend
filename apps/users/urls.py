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
)

urlpatterns = [
    path('register/', RegisterCustomerView.as_view(), name='customer-register'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('logout/', LogoutView.as_view(), name='user-logout'),
    path('me/', CurrentUserProfileView.as_view(), name='user-profile'),
    path('all/', AllUsersListView.as_view(), name='all-users-list'),
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('admins/', AdminUserListView.as_view(), name='admin-list'),
    path('<int:id>/', UserDetailUpdateView.as_view(), name='user-detail-update'),
]

