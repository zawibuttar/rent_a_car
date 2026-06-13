from django.urls import path

from .views import MapPreviewView, ThreadListView, ThreadMessagesViewThrottled, UnreadCountView

urlpatterns = [
    path('threads/', ThreadListView.as_view(), name='messaging-threads'),
    path('threads/<int:booking_id>/messages/', ThreadMessagesViewThrottled.as_view(), name='messaging-thread-messages'),
    path('unread-count/', UnreadCountView.as_view(), name='messaging-unread-count'),
    path('map-preview/', MapPreviewView.as_view(), name='messaging-map-preview'),
]
