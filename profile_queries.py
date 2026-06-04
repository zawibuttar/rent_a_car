#!/usr/bin/env python
"""
Django query profiler: Tests API endpoints and reports SQL query counts.
Run this in the Django shell or as a management command.
Usage: python manage.py shell < profile_queries.py
"""

import os
import django
from django.conf import settings
from django.test.utils import override_settings
from django.db import connection, reset_queries

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rentacar.settings')
django.setup()

from django.contrib.auth import get_user_model
from cars.models import Car, CarImage
from bookings.models import Booking
from accounts.models import OwnerProfile, CustomerProfile

User = get_user_model()

print("\n" + "="*70)
print("DJANGO QUERY PROFILER - N+1 Query Detection")
print("="*70 + "\n")

def profile_query(description, query_func):
    """Execute a query function and report SQL statistics."""
    reset_queries()
    connection.queries_log.clear()
    
    print(f"Testing: {description}")
    print("-" * 70)
    
    try:
        result = query_func()
        num_queries = len(connection.queries)
        
        if num_queries > 0:
            print(f"✓ Total queries executed: {num_queries}")
            
            # Group queries by type
            selects = sum(1 for q in connection.queries if q['sql'].strip().upper().startswith('SELECT'))
            updates = sum(1 for q in connection.queries if q['sql'].strip().upper().startswith('UPDATE'))
            inserts = sum(1 for q in connection.queries if q['sql'].strip().upper().startswith('INSERT'))
            deletes = sum(1 for q in connection.queries if q['sql'].strip().upper().startswith('DELETE'))
            
            if selects > 0:
                print(f"  - SELECT: {selects}")
            if updates > 0:
                print(f"  - UPDATE: {updates}")
            if inserts > 0:
                print(f"  - INSERT: {inserts}")
            if deletes > 0:
                print(f"  - DELETE: {deletes}")
            
            # Calculate total time
            total_time = sum(float(q['time']) for q in connection.queries)
            print(f"  - Total time: {total_time:.4f}s")
            
            # Show top slow queries
            slow_queries = sorted(connection.queries, key=lambda x: float(x['time']), reverse=True)[:3]
            if slow_queries:
                print(f"\n  Top slow queries:")
                for i, q in enumerate(slow_queries, 1):
                    time_ms = float(q['time']) * 1000
                    sql_preview = q['sql'][:80].replace('\n', ' ') + '...' if len(q['sql']) > 80 else q['sql']
                    print(f"    {i}. ({time_ms:.2f}ms) {sql_preview}")
        else:
            print(f"✗ No queries recorded")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    print()


# Test 1: Car List (PUBLIC ENDPOINT)
def test_car_list():
    from cars.serializers import CarListSerializer
    cars = Car.objects.filter(is_approved=True, is_available=True)[:10]
    serializer = CarListSerializer(cars, many=True, context={'request': None})
    return serializer.data

profile_query(
    "CarListView: List approved/available cars (with images)",
    test_car_list
)


# Test 2: Car Details
def test_car_detail():
    from cars.serializers import CarDetailSerializer
    car = Car.objects.filter(is_approved=True).prefetch_related('images').select_related('owner').first()
    if car:
        serializer = CarDetailSerializer(car, context={'request': None})
        return serializer.data
    return None

profile_query(
    "CarDetailView: Single car with images and owner",
    test_car_detail
)


# Test 3: Booking List (ADMIN ENDPOINT)
def test_booking_list():
    from bookings.serializers import BookingDetailSerializer
    bookings = Booking.objects.all().select_related('car__owner', 'customer').prefetch_related('car__images')[:10]
    serializer = BookingDetailSerializer(bookings, many=True, context={'request': None})
    return serializer.data

profile_query(
    "AdminBookingListView: All bookings with car/owner/customer (N+1 risk)",
    test_booking_list
)


# Test 4: Owner Profile List (ADMIN ENDPOINT)
def test_owner_list():
    from accounts.serializers import OwnerProfileSerializer
    owners = OwnerProfile.objects.all().select_related('user')[:10]
    serializer = OwnerProfileSerializer(owners, many=True, context={'request': None})
    return serializer.data

profile_query(
    "AdminOwnerListView: All owner profiles with user",
    test_owner_list
)


# Test 5: My Bookings (CUSTOMER ENDPOINT - simulate)
def test_my_bookings():
    from bookings.serializers import BookingDetailSerializer
    # Simulate getting current user's bookings
    bookings = Booking.objects.filter(customer__username='admin').select_related('car__owner', 'customer').prefetch_related('car__images')[:5]
    serializer = BookingDetailSerializer(bookings, many=True, context={'request': None})
    return serializer.data

profile_query(
    "MyBookingsView: User's bookings with car/images",
    test_my_bookings
)


# Test 6: My Cars (OWNER ENDPOINT - simulate)
def test_my_cars():
    from cars.serializers import CarDetailSerializer
    # Simulate getting owner's cars
    cars = Car.objects.filter(owner__username='admin').select_related('owner').prefetch_related('images')[:5]
    serializer = CarDetailSerializer(cars, many=True, context={'request': None})
    return serializer.data

profile_query(
    "MyCarListView: Owner's cars with images and owner",
    test_my_cars
)


print("="*70)
print("SUMMARY")
print("="*70)
print("""
If you see HIGH query counts (e.g., 20+ queries for 10 items), there are N+1 issues.
Expected counts (with proper prefetch/select):
  - CarListView (10 cars): ~2 queries (1 car list + 1 image prefetch)
  - CarDetailView (1 car): ~1 query
  - BookingListView (10 bookings): ~2-3 queries (1 booking + prefetch car/customer)
  - OwnerListView (10 owners): ~2 queries (1 owner + 1 user select)
  - MyBookingsView (5 bookings): ~2 queries
  - MyCarListView (5 cars): ~2 queries
""")
print("="*70 + "\n")
