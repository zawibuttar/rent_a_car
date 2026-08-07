from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin

# Register your models here.

admin.site.register(User, UserAdmin)
admin.site.register(CustomerProfile)
admin.site.register(OwnerProfile)
admin.site.register(SocialMediaLink)


@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'width', 'height', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title']