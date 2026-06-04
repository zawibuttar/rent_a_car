"""
URL configuration for rentacar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from .import page_views
from .health_views import HealthView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', HealthView.as_view(), name='health'),
    path('api/accounts/', include('accounts.urls')),
    path('api/cars/', include('cars.urls')),
    path('api/bookings/', include('bookings.urls')),

# Frontend pages
    path('', page_views.home, name='home'),
    path('cars/', page_views.car_list, name='car-list-page'),
    path('cars/<int:pk>/', page_views.car_detail, name='car-detail-page'),
    path('login/', page_views.login_page, name='login-page'),
    path('register/', page_views.register_page, name='register-page'),
    path('dashboard/', page_views.main_dashboard, name='main-dashboard'),
    path('dashboard/customer/', page_views.customer_dashboard, name='customer-dashboard'),
    path('dashboard/owner/', page_views.owner_dashboard, name='owner-dashboard'),
    path('dashboard/admin/', page_views.admin_dashboard, name='admin-dashboard'),
    # Browser requests to /favicon.ico are redirected to the static favicon asset.
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.svg', permanent=False)),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
