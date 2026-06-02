from django.shortcuts import render
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from accounts.permissions import IsCustomer, IsOwner, IsPlatformAdmin
from rentacar.caching import CacheHeadersMixin

# Create your views here.

class BookingCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            booking = serializer.save()
            booking = Booking.objects.select_related('car__owner', 'customer').prefetch_related('car__images').get(pk=booking.pk)
            return Response({
                "message": "Booking request submitted successfully.",
                "booking": BookingDetailSerializer(booking, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyBookingsView(CacheHeadersMixin, generics.ListAPIView):
    serializer_class   = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    pagination_class   = None
    cache_timeout = 300  # Cache for 5 minutes (user-specific data)

    def get_queryset(self):
        return Booking.objects.filter(
            customer=self.request.user
        ).select_related('car__owner', 'customer').prefetch_related('car__images')


class BookingDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        booking = get_object_or_404(
            Booking.objects.select_related('car__owner', 'customer').prefetch_related('car__images'),
            pk=pk
        )
        is_customer  = booking.customer == request.user
        is_car_owner = booking.car.owner == request.user

        if not (is_customer or is_car_owner or request.user.is_platform_admin):
            return Response({"error": "You do not have permission to view this booking."}, status=status.HTTP_403_FORBIDDEN)

        serializer = BookingDetailSerializer(booking, context={'request': request})
        return Response(serializer.data)


class CancelBookingView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    def patch(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, customer=request.user)

        if booking.status not in ['pending', 'approved']:
            return Response({"error": f"Cannot cancel a booking with status '{booking.status}'."}, status=status.HTTP_400_BAD_REQUEST)

        booking.status = 'cancelled'
        booking.save()
        return Response({
            "message": "Booking cancelled successfully.",
            "booking_id": booking.id,
            "status": booking.status,
        }, status=status.HTTP_200_OK)


class OwnerBookingsView(CacheHeadersMixin, generics.ListAPIView):
    serializer_class   = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    pagination_class   = None
    cache_timeout = 300  # Cache for 5 minutes

    def get_queryset(self):
        return Booking.objects.filter(
            car__owner=self.request.user
        ).select_related('car__owner', 'customer').prefetch_related('car__images')


class BookingStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def patch(self, request, pk):
        booking = get_object_or_404(
            Booking.objects.select_related('car__owner', 'customer').prefetch_related('car__images'),
            pk=pk, car__owner=request.user
        )

        if booking.status != 'pending':
            return Response(
                {"error": "Only pending bookings can be approved or rejected."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BookingStatusSerializer(booking, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "message" : f"Booking has been {booking.status}.",
                "booking" : BookingDetailSerializer(booking, context={'request': request}).data,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompleteBookingView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def patch(self, request, pk):
        booking = get_object_or_404(
            Booking.objects.select_related('car__owner', 'customer').prefetch_related('car__images'),
            pk=pk, car__owner=request.user
        )

        if booking.status != 'approved':
            return Response(
                {"error": "Only approved bookings can be marked as completed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = 'completed'
        booking.save()
        # Fetch owner_profile directly to avoid N+1 when user has many profiles
        from accounts.models import OwnerProfile
        owner_profile = OwnerProfile.objects.get(user=request.user)
        owner_profile.total_earnings += booking.total_cost
        owner_profile.save()
        return Response({
            "message"        : "Booking marked as completed.",
            "booking_id"     : booking.id,
            "total_cost"     : booking.total_cost,
            "total_earnings" : owner_profile.total_earnings,
        }, status=status.HTTP_200_OK)


class ReviewCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    def post(self, request):
        serializer = ReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            review = serializer.save()
            return Response({
                "message": "Review submitted successfully.",
                "review" : ReviewSerializer(review).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminBookingListView(CacheHeadersMixin, generics.ListAPIView):
    serializer_class   = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset           = Booking.objects.all().select_related('car__owner', 'customer').prefetch_related('car__images')
    pagination_class = None
    cache_timeout = 300  # Cache for 5 minutes


class AdminBookingActionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def patch(self, request, pk):
        booking = get_object_or_404(
            Booking.objects.select_related('car__owner', 'customer').prefetch_related('car__images'),
            pk=pk
        )
        new_status = request.data.get('status')
        allowed = ['approved', 'rejected', 'cancelled', 'completed']
        if new_status not in allowed:
            return Response(
                {"error": f"Status must be one of: {', '.join(allowed)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        booking.status = new_status
        booking.save()
        return Response({
            "message"    : f"Booking status updated to '{new_status}'.",
            "booking_id" : booking.id,
            "status"     : booking.status,
        }, status=status.HTTP_200_OK)