# trips/models.py
from django.db import models

class Trip(models.Model):
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    distance = models.FloatField(null=True, blank=True)  # in miles
    hours_used = models.FloatField(default=0)            # HOS cycle used so far
    departure_time = models.DateTimeField(null=True, blank=True)
    route_polyline = models.TextField(null=True, blank=True)  # Stores route geometry info
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip from {self.pickup_location} to {self.dropoff_location}"

class DailyLog(models.Model):
    trip = models.ForeignKey(Trip, related_name='daily_logs', on_delete=models.CASCADE)
    day_number = models.IntegerField()
    driving_hours = models.FloatField(default=0)
    off_duty_hours = models.FloatField(default=0)
    on_duty_hours = models.FloatField(default=0)
    cumulative_hours = models.FloatField(default=0)
    reset_applied = models.BooleanField(default=False)
    rest_break_taken = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)
    # New fields for fueling details and stop markers
    fueling_stop_details = models.TextField(blank=True, null=True)
    stop_markers = models.TextField(blank=True, null=True)  # Store JSON string of detailed markers
    log_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Day {self.day_number} Log for Trip {self.trip.id}"
