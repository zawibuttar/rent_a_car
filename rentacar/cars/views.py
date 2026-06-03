from django.db.models import OuterRef, Subquery
from rest_framework import status, generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .serializers import *
from accounts.permissions import IsOwner, IsPlatformAdmin
from rentacar.caching import (
    NoCacheMixin,
    RedisListCacheMixin,
    admin_cars_key,
    invalidate_car_caches,
)
from rentacar.utils import parse_bool
from rentacar.image_validation import validate_car_image_file

# Create your views here.

# Customer sides
class CarListView(NoCacheMixin, generics.ListAPIView):
    serializer_class   = CarListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields  = ['brand', 'model', 'location']
    ordering_fields = ['price_per_day', 'year', 'created_at']
    ordering        = ['-created_at']
    filterset_fields = ['car_type', 'is_available', 'brand']

    def get_queryset(self):
        primary_image_subquery = CarImage.objects.filter(
            car=OuterRef('pk')
        ).order_by('-is_primary', 'id').values('image')[:1]

        queryset = Car.objects.filter(
            is_approved=True,
            is_available=True,
        ).select_related('owner').prefetch_related('images').only(
            'id', 'brand', 'model', 'year', 'car_type', 'price_per_day', 'location', 'is_available',
            'owner__username'
        ).annotate(primary_image=Subquery(primary_image_subquery))

        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if min_price:
            queryset = queryset.filter(price_per_day__gte=min_price)
        if max_price:
            queryset = queryset.filter(price_per_day__lte=max_price)
        return queryset


class CarDetailView(NoCacheMixin, generics.RetrieveAPIView):
    serializer_class   = CarDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Car.objects.filter(is_approved=True).prefetch_related('images').select_related('owner')


# Owner sides
class CarCreateView(generics.CreateAPIView):
    serializer_class   = CarCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_serializer_context(self):
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            car = serializer.save()
            invalidate_car_caches()
            return Response({
                "message" : "Car listed successfully!",
                "car"     : CarDetailSerializer(car, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyCarListView(NoCacheMixin, generics.ListAPIView):
    serializer_class   = CarDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Car.objects.filter(owner=self.request.user).select_related('owner').prefetch_related('images')


class CarUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = CarCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Car.objects.filter(owner=self.request.user).select_related('owner').prefetch_related('images')

    def get_serializer_context(self):
        return {'request': self.request}

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data['message'] = "Car updated successfully."
        invalidate_car_caches()
        return response

    def destroy(self, request, *args, **kwargs):
        car = self.get_object()
        car.delete()
        invalidate_car_caches()
        return Response(
            {"message": "Car listing deleted successfully."},
            status=status.HTTP_200_OK
        )


class CarImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    parser_classes     = [MultiPartParser, FormParser]

    def post(self, request, pk):
        car = get_object_or_404(
            Car.objects.prefetch_related('images'),
            pk=pk, owner=request.user
        )
        images = request.FILES.getlist('images')

        if not images:
            return Response(
                {"error": "No images provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_count = car.images.count()
        if existing_count + len(images) > settings.CAR_IMAGE_MAX_COUNT:
            return Response(
                {"error": f"Maximum {settings.CAR_IMAGE_MAX_COUNT} images per car."},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded = []
        for index, image_file in enumerate(images):
            err = validate_car_image_file(image_file)
            if err:
                return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)
            is_primary = (index == 0) and not car.images.exists()
            img = CarImage.objects.create(car=car, image=image_file, is_primary=is_primary)
            uploaded.append(CarImageUploadSerializer(img).data)
        invalidate_car_caches()
        return Response({
            "message": f"{len(uploaded)} image(s) uploaded successfully.",
            "images" : uploaded,
        }, status=status.HTTP_201_CREATED)


class CarImageDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def delete(self, request, pk):
        image = get_object_or_404(
            CarImage.objects.select_related('car__owner'),
            pk=pk, car__owner=request.user
        )
        image.delete()
        invalidate_car_caches()
        return Response(
            {"message": "Image deleted successfully."},
            status=status.HTTP_200_OK
        )


# Admin sides
class AdminCarListView(RedisListCacheMixin, NoCacheMixin, generics.ListAPIView):
    serializer_class   = AdminCarListSerializer
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]
    queryset           = Car.objects.all().select_related('owner')
    redis_cache_key = admin_cars_key()


class AdminCarApprovalView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def patch(self, request, pk):
        car        = get_object_or_404(Car, pk=pk)
        raw = request.data.get('is_approved')
        if raw is None:
            return Response(
                {"error": "Please provide 'is_approved': true or false."},
                status=status.HTTP_400_BAD_REQUEST
            )
        is_approved = parse_bool(raw)
        car.is_approved = is_approved
        car.save()
        invalidate_car_caches()
        action = "approved" if is_approved else "rejected"
        return Response({
            "message": f"Car has been {action}.",
            "car_id" : car.id,
            "is_approved": car.is_approved,
        }, status=status.HTTP_200_OK)
