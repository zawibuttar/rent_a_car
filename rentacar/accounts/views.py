from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from .models import *
from .serializers import *
from .permissions import IsPlatformAdmin
from rentacar.caching import (
    ADMIN_OWNERS_KEY,
    NoCacheMixin,
    PublicCacheHeadersMixin,
    RedisListCacheMixin,
    invalidate_admin_lists,
    invalidate_social_media_cache,
)
from rentacar.throttling import AdminRateThrottle, AuthRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters
from .filters import AdminOwnerFilter

# Create your views here.

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'User registered successfully.',
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Failed to register user.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'message': 'User logged in successfully.',
                'user': UserSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_200_OK)
        return Response({
            'message': 'Failed to log in user.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)   


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        logout(request)
        return Response({'message': 'User logged out successfully.'}, status=status.HTTP_200_OK)
    



class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data

        if user.is_customer:
            try:
                profile = CustomerProfileSerializer(user.customer_profile).data
            except CustomerProfile.DoesNotExist:
                profile = None
            data['customer_profile'] = profile

        elif user.is_owner:
            try:
                profile = OwnerProfileSerializer(user.owner_profile).data
            except OwnerProfile.DoesNotExist:
                profile = None
            data['owner_profile'] = profile
        return Response(data, status=status.HTTP_200_OK)


class CustomerProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CustomerProfileSerializer

    def get_object(self):
        profile, _ = CustomerProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_customer:
            return Response({'message': 'Only customers can access this endpoint.'}, status=status.HTTP_403_FORBIDDEN)
        return super().get(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        if not request.user.is_customer:
            return Response({'message': 'Only customers can access this endpoint.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class OwnerProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OwnerProfileSerializer

    def get_object(self):
        profile, _ = OwnerProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_owner:
            return Response({'message': 'Only owners can access this endpoint.'}, status=status.HTTP_403_FORBIDDEN)
        return super().get(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        if not request.user.is_owner:
            return Response({'message': 'Only owners can access this endpoint.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class AdminOwnerListView(RedisListCacheMixin, NoCacheMixin, generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    throttle_classes = [AdminRateThrottle]
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter, DjangoFilterBackend]
    filterset_class = AdminOwnerFilter
    search_fields = ['user__username', 'user__email', 'phone_number']
    ordering_fields = ['user__username', 'created_at']
    ordering = ['user__username']
    serializer_class = OwnerProfileSerializer
    queryset = OwnerProfile.objects.all().select_related('user')
    redis_cache_key = ADMIN_OWNERS_KEY


class AdminOwnerVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def patch(self, request, pk):
        profile = get_object_or_404(
            OwnerProfile.objects.select_related('user'),
            pk=pk
        )
        if not request.user.is_platform_admin:
            return Response({'message': 'Only admins can manage owner verification.'}, status=status.HTTP_403_FORBIDDEN)

        is_verified = request.data.get('is_verified')
        if is_verified is None:
            return Response({
                'error': "Please provide 'is_verified': true or false."
            }, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(is_verified, str):
            is_verified = is_verified.lower() in ['true', '1', 'yes']

        profile.is_verified = bool(is_verified)
        profile.save()
        invalidate_admin_lists()
        return Response({
            'message': f"Owner profile has been {'verified' if profile.is_verified else 'marked as unverified' }.",
            'owner_profile': OwnerProfileSerializer(profile).data
        }, status=status.HTTP_200_OK)


class PublicSocialMediaLinkListView(PublicCacheHeadersMixin, generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = SocialMediaLinkSerializer
    queryset = SocialMediaLink.objects.filter(is_active=True)
    pagination_class = None


class AdminSocialMediaLinkListCreateView(NoCacheMixin, generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    throttle_classes = [AdminRateThrottle]
    serializer_class = SocialMediaLinkSerializer
    queryset = SocialMediaLink.objects.all()
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save()
        invalidate_social_media_cache()


class AdminSocialMediaLinkDetailView(NoCacheMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    throttle_classes = [AdminRateThrottle]
    serializer_class = SocialMediaLinkSerializer
    queryset = SocialMediaLink.objects.all()

    def perform_update(self, serializer):
        serializer.save()
        invalidate_social_media_cache()

    def perform_destroy(self, instance):
        instance.delete()
        invalidate_social_media_cache()


class AdminHeroBannerListCreateView(NoCacheMixin, generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    throttle_classes = [AdminRateThrottle]
    serializer_class = HeroBannerSerializer
    queryset = HeroBanner.objects.all()
    pagination_class = None


class AdminHeroBannerDetailView(NoCacheMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    throttle_classes = [AdminRateThrottle]
    serializer_class = HeroBannerSerializer
    queryset = HeroBanner.objects.all()


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'message': 'Password is incorrect.'} , status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            Token.objects.filter(user=user).delete()
            return Response({'message': 'Password changed successfully. Please log in again.'}, status=status.HTTP_200_OK)
        
        return Response({'message': 'Failed to change password.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
