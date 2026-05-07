from django.contrib import admin

from .models import RideEvent


@admin.register(RideEvent)
class RideEventAdmin(admin.ModelAdmin):
    list_display = ('id_ride_event', 'id_ride', 'description', 'created_at')
    search_fields = ('description',)
    list_filter = ('created_at',)
