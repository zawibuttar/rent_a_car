"""Aggregate customer reviews per car (via completed bookings)."""
from django.db.models import Avg, Count, FloatField, IntegerField, OuterRef, Subquery

from bookings.models import Review


def annotate_car_review_stats(queryset):
    """Subqueries avoid joining bookings on the car queryset (keeps booking prefetch)."""
    reviews = Review.objects.filter(booking__car_id=OuterRef('pk'))
    review_count_sq = (
        reviews.values('booking__car_id')
        .annotate(cnt=Count('pk'))
        .values('cnt')[:1]
    )
    average_rating_sq = (
        reviews.values('booking__car_id')
        .annotate(avg=Avg('rating'))
        .values('avg')[:1]
    )
    return queryset.annotate(
        review_count=Subquery(review_count_sq, output_field=IntegerField()),
        average_rating=Subquery(average_rating_sq, output_field=FloatField()),
    )


def get_car_review_summary(car):
    qs = Review.objects.filter(booking__car=car)
    agg = qs.aggregate(avg=Avg('rating'), count=Count('id'))
    count = agg['count'] or 0
    distribution = {str(i): 0 for i in range(5, 0, -1)}
    if count:
        for row in qs.values('rating').annotate(n=Count('id')):
            distribution[str(row['rating'])] = row['n']
    average = round(float(agg['avg']), 1) if agg['avg'] is not None else None
    return {
        'count': count,
        'average_rating': average,
        'distribution': distribution,
    }


def get_car_reviews(car, limit=20):
    return (
        Review.objects.filter(booking__car=car)
        .select_related('reviewer')
        .order_by('-created_at')[:limit]
    )
