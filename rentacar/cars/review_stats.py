"""Aggregate customer reviews per car (via completed bookings)."""
from django.db.models import Avg, Count

from bookings.models import Review


def annotate_car_review_stats(queryset):
    return queryset.annotate(
        review_count=Count('bookings__review', distinct=True),
        average_rating=Avg('bookings__review__rating'),
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
