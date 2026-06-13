from django.urls import path

from .views import (
    AdminAnnouncementDetailView,
    AdminAnnouncementListCreateView,
    AnnouncementBannerView,
    AnnouncementDismissBannerView,
    AnnouncementListView,
    AnnouncementReadView,
    AnnouncementUnreadCountView,
)

urlpatterns = [
    path('', AnnouncementListView.as_view(), name='announcement-list'),
    path('unread-count/', AnnouncementUnreadCountView.as_view(), name='announcement-unread-count'),
    path('banner/', AnnouncementBannerView.as_view(), name='announcement-banner'),
    path('<int:pk>/read/', AnnouncementReadView.as_view(), name='announcement-read'),
    path('<int:pk>/dismiss-banner/', AnnouncementDismissBannerView.as_view(), name='announcement-dismiss-banner'),
    path('admin/', AdminAnnouncementListCreateView.as_view(), name='announcement-admin-list'),
    path('admin/<int:pk>/', AdminAnnouncementDetailView.as_view(), name='announcement-admin-detail'),
]
