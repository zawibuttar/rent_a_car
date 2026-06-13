from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from rentacar.message_attachment_validation import validate_message_attachment_file
from rentacar.throttling import BookingRateThrottle

from .map_preview import map_preview_response
from .permissions import can_post_message
from .serializers import MessageSerializer, SendMessageSerializer, ThreadContextSerializer, ThreadSummarySerializer
from .services import (
    counterparty_read_at,
    create_attachment_message,
    create_location_message,
    create_text_message,
    get_booking_for_user,
    mark_thread_read,
    thread_context_for_booking,
    thread_summaries_for_user,
    total_unread_count,
)
from .models import BookingMessage


class ThreadListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        summaries = thread_summaries_for_user(request.user)
        data = ThreadSummarySerializer(summaries, many=True).data
        return Response({'data': data})


class UnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({'data': {'count': total_unread_count(request.user)}})


class ThreadMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, booking_id):
        booking = get_booking_for_user(request.user, booking_id)
        if not booking:
            return Response({'error': 'Thread not found.'}, status=status.HTTP_404_NOT_FOUND)

        mark_thread_read(booking, request.user)
        messages = booking.messages.select_related('sender').order_by('created_at')
        read_at = counterparty_read_at(booking, request.user)
        serializer = MessageSerializer(
            messages,
            many=True,
            context={'request': request, 'counterparty_read_at': read_at},
        )
        return Response({
            'data': {
                'messages': serializer.data,
                'total': messages.count(),
                'booking_status': booking.status,
                'is_open': booking.status in {'pending', 'approved'},
                'context': ThreadContextSerializer(
                    thread_context_for_booking(booking, request.user, request)
                ).data,
            },
        })

    def post(self, request, booking_id):
        booking = get_booking_for_user(request.user, booking_id)
        if not booking:
            return Response({'error': 'Thread not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not can_post_message(request.user, booking):
            return Response(
                {'error': 'This booking thread is closed or you cannot post messages.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        upload_file = request.FILES.get('file')
        message_type = request.data.get('message_type') or BookingMessage.MessageType.TEXT
        if upload_file or message_type == BookingMessage.MessageType.ATTACHMENT:
            if not upload_file:
                return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)
            err = validate_message_attachment_file(upload_file)
            if err:
                return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
            caption = (request.data.get('body') or '').strip()
            message = create_attachment_message(booking, request.user, upload_file, caption=caption)
        else:
            serializer = SendMessageSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated = serializer.validated_data
            if validated.get('message_type') == BookingMessage.MessageType.LOCATION:
                message = create_location_message(
                    booking,
                    request.user,
                    latitude=float(validated['latitude']),
                    longitude=float(validated['longitude']),
                    label=validated.get('body', ''),
                    accuracy=validated.get('accuracy'),
                )
            else:
                message = create_text_message(booking, request.user, validated['body'])

        mark_thread_read(booking, request.user)
        read_at = counterparty_read_at(booking, request.user)
        out = MessageSerializer(
            message,
            context={'request': request, 'counterparty_read_at': read_at},
        )
        return Response({'data': out.data}, status=status.HTTP_201_CREATED)


class ThreadMessagesViewThrottled(ThreadMessagesView):
    throttle_classes = [BookingRateThrottle]

    def post(self, request, booking_id):
        return super().post(request, booking_id)


class MapPreviewView(APIView):
    """Public tile proxy so <img> tags can load without auth headers."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            lat = float(request.query_params.get('lat', ''))
            lng = float(request.query_params.get('lng', ''))
            zoom = int(request.query_params.get('z', 14))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid coordinates.'}, status=status.HTTP_400_BAD_REQUEST)

        if lat < -90 or lat > 90 or lng < -180 or lng > 180:
            return Response({'error': 'Coordinates out of range.'}, status=status.HTTP_400_BAD_REQUEST)
        if zoom < 1 or zoom > 18:
            zoom = 14

        return map_preview_response(lat, lng, zoom)
