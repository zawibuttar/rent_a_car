from django.urls import path
from .views import *

urlpatterns = [
    path('', CarListView.as_view(), name='car-list'),
    path('<int:pk>/', CarDetailView.as_view(), name='car-detail'),

    path('create/', CarCreateView.as_view(), name='car-create'),
    path('my-cars/', MyCarListView.as_view(), name='my-car'),
    path('<int:pk>/manage/', CarUpdateDeleteView.as_view(), name='car-manage'),
    path('<int:pk>/images/', CarImageUploadView.as_view(), name='car-image-upload'),
    path('images/<int:pk>/delete/', CarImageDeleteView.as_view(), name='car-image-delete'),

    path('admin/all/', AdminCarListView.as_view(), name='admin-car-list'),
    path('admin/<int:pk>/approve/', AdminCarApprovalView.as_view(), name='admin-car-approve'),
]