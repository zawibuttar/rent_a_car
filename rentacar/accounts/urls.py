from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('me/', views.MeView.as_view(), name='me'),
    path('profile/customer/', views.CustomerProfileView.as_view(), name='customer-profile'),
    path('profile/owner/', views.OwnerProfileView.as_view(), name='owner-profile'),
    path('admin/owners/', views.AdminOwnerListView.as_view(), name='admin-owner-list'),
    path('admin/owners/<int:pk>/verify/', views.AdminOwnerVerificationView.as_view(), name='admin-owner-verify'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
]