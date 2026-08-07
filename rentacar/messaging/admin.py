from django.contrib import admin

from .models import BookingMessage, BookingThreadRead


@admin.register(BookingMessage)
class BookingMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'sender', 'message_type', 'created_at']
    list_filter = ['message_type']
    search_fields = ['body', 'booking__id']


@admin.register(BookingThreadRead)
class BookingThreadReadAdmin(admin.ModelAdmin):
    list_display = ['booking', 'user', 'last_read_at']
