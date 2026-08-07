"""
Vehicle taxonomy for RentACar listings.

Three separate concepts (do not conflate):
  1. Vehicle category (Car.category) — marketplace segment: car, luxury_car, loader
  2. Vehicle type (Car.car_type) — body/chassis within a category: sedan, tipper_dumper, etc.
  3. Rental duration (Booking.rental_type / Car.rent_*) — how long a customer rents: hourly, daily, …
"""
from django.db import models


class CarCategory(models.TextChoices):
    CAR = 'car', 'Cars'
    LUXURY_CAR = 'luxury_car', 'Luxury'
    LOADER = 'loader', 'Loaders'


CATEGORY_DESCRIPTIONS = {
    CarCategory.CAR: 'Standard passenger vehicles for daily use',
    CarCategory.LUXURY_CAR: 'Premium brands, high-end features, executive and sports',
    CarCategory.LOADER: 'Commercial, construction, and heavy transport',
}


class CarType(models.TextChoices):
    # Cars
    HATCHBACK = 'hatchback', 'Hatchback'
    SEDAN = 'sedan', 'Sedan'
    SUV = 'suv', 'SUV'
    MUV_MPV = 'muv_mpv', 'MUV / MPV'
    CROSSOVER = 'crossover', 'Crossover'
    CONVERTIBLE = 'convertible', 'Convertible'
    COUPE = 'coupe', 'Coupe'
    PICKUP_TRUCK = 'pickup_truck', 'Pickup Truck'
    # Luxury
    LUXURY_SEDAN = 'luxury_sedan', 'Luxury Sedan'
    LUXURY_SUV = 'luxury_suv', 'Luxury SUV'
    SPORTS_CAR = 'sports_car', 'Sports Car'
    LUXURY_CONVERTIBLE = 'luxury_convertible', 'Luxury Convertible'
    LUXURY_COUPE = 'luxury_coupe', 'Luxury Coupe'
    LIMOUSINE = 'limousine', 'Limousine'
    ELECTRIC_LUXURY = 'electric_luxury', 'Electric Luxury'
    LUXURY_CROSSOVER = 'luxury_crossover', 'Luxury Crossover'
    # Loaders
    MINI_TRUCK = 'mini_truck', 'Mini Truck'
    PICKUP_LOADER = 'pickup_loader', 'Commercial Pickup'
    CONTAINER_TRUCK = 'container_truck', 'Container Truck'
    TIPPER_DUMPER = 'tipper_dumper', 'Tipper / Dumper'
    FLATBED_TRUCK = 'flatbed_truck', 'Flatbed Truck'
    REFRIGERATED_TRUCK = 'refrigerated_truck', 'Refrigerated Truck'
    TANKER_TRUCK = 'tanker_truck', 'Tanker Truck'
    CRANE_TRUCK = 'crane_truck', 'Crane Truck'


CATEGORY_TYPE_MAP = {
    CarCategory.CAR: [
        CarType.HATCHBACK, CarType.SEDAN, CarType.SUV, CarType.MUV_MPV,
        CarType.CROSSOVER, CarType.CONVERTIBLE, CarType.COUPE, CarType.PICKUP_TRUCK,
    ],
    CarCategory.LUXURY_CAR: [
        CarType.LUXURY_SEDAN, CarType.LUXURY_SUV, CarType.SPORTS_CAR,
        CarType.LUXURY_CONVERTIBLE, CarType.LUXURY_COUPE, CarType.LIMOUSINE,
        CarType.ELECTRIC_LUXURY, CarType.LUXURY_CROSSOVER,
    ],
    CarCategory.LOADER: [
        CarType.MINI_TRUCK, CarType.PICKUP_LOADER, CarType.CONTAINER_TRUCK,
        CarType.TIPPER_DUMPER, CarType.FLATBED_TRUCK, CarType.REFRIGERATED_TRUCK,
        CarType.TANKER_TRUCK, CarType.CRANE_TRUCK,
    ],
}

DEFAULT_CATEGORY = CarCategory.CAR


def types_for_category(category):
    """Return list of CarType values allowed for the given category string."""
    try:
        cat = CarCategory(category)
    except ValueError:
        return []
    return [t.value for t in CATEGORY_TYPE_MAP.get(cat, [])]


def get_category_label(category):
    try:
        return CarCategory(category).label
    except ValueError:
        return category or ''


def get_car_type_label(car_type):
    try:
        return CarType(car_type).label
    except ValueError:
        return car_type or ''


def validate_category_type_pair(category, car_type):
    """Return error message if invalid, else None."""
    if not category or not car_type:
        return 'Both category and vehicle type are required.'
    try:
        CarCategory(category)
    except ValueError:
        return f'Invalid category: {category}.'
    try:
        CarType(car_type)
    except ValueError:
        return f'Invalid vehicle type: {car_type}.'
    allowed = types_for_category(category)
    if car_type not in allowed:
        cat_label = get_category_label(category)
        type_label = get_car_type_label(car_type)
        return (
            f'{type_label} is not valid for the {cat_label} category. '
            f'Choose a type that matches the selected category.'
        )
    return None


def taxonomy_payload():
    """Serialize full taxonomy for API / frontend."""
    from bookings.enums import RentalDuration

    categories = []
    for cat in CarCategory:
        types = CATEGORY_TYPE_MAP.get(cat, [])
        categories.append({
            'value': cat.value,
            'label': cat.label,
            'description': CATEGORY_DESCRIPTIONS.get(cat, ''),
            'types': [{'value': t.value, 'label': t.label} for t in types],
        })
    return {
        'categories': categories,
        'rental_durations': [
            {'value': d.value, 'label': d.label} for d in RentalDuration
        ],
        'default_category': DEFAULT_CATEGORY,
    }
