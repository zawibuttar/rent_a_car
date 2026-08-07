from django.contrib import admin
from .models import Car, CarImage


class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 1
    fields = ['image', 'is_primary']
    readonly_fields = []


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = [
        'brand', 'model', 'year', 'owner',
        'category', 'car_type',
        'price_per_day', 'discount_percentage', 'discounted_price', 'is_available', 'is_approved',
        'created_at',
    ]
    list_filter  = ['category', 'car_type', 'is_available', 'is_approved']
    list_editable = ['is_available', 'is_approved']
    search_fields = ['brand', 'model', 'location', 'owner__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CarImageInline]

    fieldsets = (
        ('Vehicle Identity', {
            'fields': ('owner', 'brand', 'model', 'year', 'description'),
        }),
        ('Category & Type', {
            'fields': ('category', 'car_type'),
            'description': (
                'category: car | luxury_car | loader  '
                '— select a car_type matching the chosen category.'
            ),
        }),
        ('Location', {
            'fields': ('location',),
        }),
        ('Rental Options', {
            'fields': (
                ('rent_hourly', 'price_per_hour'),
                ('rent_daily',  'price_per_day'),
                ('rent_weekly', 'price_per_week'),
                ('rent_monthly','price_per_month'),
            ),
        }),
        ('Discounts', {
            'fields': ('discount_percentage', 'discounted_price'),
            'description': 'Configure a discount (percentage or fixed discounted price) for this vehicle.',
        }),
        ('Status', {
            'fields': ('is_available', 'is_approved', 'created_at', 'updated_at'),
        }),
    )