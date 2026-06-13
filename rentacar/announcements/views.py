from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsPlatformAdmin

from .models import Announcement
from .serializers import AnnouncementSerializer, AnnouncementWriteSerializer
from .services import (
    active_announcements_queryset,
    announcements_for_user,
    banner_announcement_for_user,
    dismiss_announcement_banner,
    mark_announcement_read,
    unread_count_for_user,
)


def _read_map_for_user(user, announcement_ids):
    from .models import AnnouncementRead
    return {
        r.announcement_id: r
        for r in AnnouncementRead.objects.filter(user=user, announcement_id__in=announcement_ids)
    }


def _serialize_list(queryset, request):
    items = list(queryset)
    read_map = _read_map_for_user(request.user, [a.id for a in items])
    return AnnouncementSerializer(
        items,
        many=True,
        context={'request': request, 'read_map': read_map},
    ).data


class AnnouncementListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = _serialize_list(announcements_for_user(request.user), request)
        return Response({'data': data})


class AnnouncementUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({'data': {'count': unread_count_for_user(request.user)}})


class AnnouncementBannerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ann = banner_announcement_for_user(request.user)
        if not ann:
            return Response({'data': None})
        read_map = _read_map_for_user(request.user, [ann.id])
        data = AnnouncementSerializer(ann, context={'request': request, 'read_map': read_map}).data
        return Response({'data': data})


class AnnouncementReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        ann = active_announcements_queryset(request.user).filter(pk=pk).first()
        if not ann:
            return Response({'error': 'Announcement not found.'}, status=status.HTTP_404_NOT_FOUND)
        mark_announcement_read(ann, request.user)
        return Response({'data': {'ok': True}})


class AnnouncementDismissBannerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        ann = active_announcements_queryset(request.user).filter(pk=pk).first()
        if not ann:
            return Response({'error': 'Announcement not found.'}, status=status.HTTP_404_NOT_FOUND)
        dismiss_announcement_banner(ann, request.user)
        return Response({'data': {'ok': True}})


class AdminAnnouncementListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        items = Announcement.objects.select_related('created_by').order_by('-published_at')
        data = AnnouncementSerializer(items, many=True, context={'request': request, 'read_map': {}}).data
        return Response({'data': data})

    def post(self, request):
        serializer = AnnouncementWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        ann = serializer.save(created_by=request.user)
        data = AnnouncementSerializer(ann, context={'request': request, 'read_map': {}}).data
        return Response({'data': data}, status=status.HTTP_201_CREATED)


class AdminAnnouncementDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPlatformAdmin]

    def get_object(self, pk):
        return Announcement.objects.filter(pk=pk).first()

    def patch(self, request, pk):
        ann = self.get_object(pk)
        if not ann:
            return Response({'error': 'Announcement not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AnnouncementWriteSerializer(ann, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        ann = serializer.save()
        data = AnnouncementSerializer(ann, context={'request': request, 'read_map': {}}).data
        return Response({'data': data})

    def delete(self, request, pk):
        ann = self.get_object(pk)
        if not ann:
            return Response({'error': 'Announcement not found.'}, status=status.HTTP_404_NOT_FOUND)
        ann.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
