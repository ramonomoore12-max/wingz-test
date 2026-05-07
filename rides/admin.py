from django.contrib import admin

from .models import Ride


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id_ride', 'status', 'id_rider', 'id_driver', 'pickup_time')
    search_fields = ('id_rider__email', 'id_driver__email')
    list_filter = ('status',)
