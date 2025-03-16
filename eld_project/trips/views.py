import json
import math
import googlemaps
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Trip, DailyLog
from .services import get_route
from .hos_calculator import calculate_daily_logs, generate_pdf_log, generate_image_log

@csrf_exempt  # Add this if you are not sending CSRF tokens from the frontend
def create_trip(request):
    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = request.POST

        current_location = data.get('current_location')
        pickup_location = data.get('pickup_location')
        dropoff_location = data.get('dropoff_location')
        hours_used = float(data.get('hours_used', 0))
        departure_time = data.get('departure_time')

        # Convert departure_time to a timezone-aware datetime if provided
        if departure_time:
            departure_time = datetime.strptime(departure_time, '%Y-%m-%dT%H:%M')
            departure_time = timezone.make_aware(departure_time)

        route_info = get_route(pickup_location, dropoff_location)
        if not route_info:
            return JsonResponse({'error': 'Error obtaining route information.'}, status=400)

        # Get the encoded polyline directly
        encoded_polyline = route_info.get('geometry')
        
        # Create the Trip object
        trip = Trip.objects.create(
            current_location=current_location,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            distance=route_info['distance'],
            hours_used=hours_used,
            departure_time=departure_time,
            route_polyline=encoded_polyline  # Store encoded polyline string directly
        )

        # Calculate daily logs
        daily_logs_data = calculate_daily_logs(trip.distance, hours_used, departure_time)
        for log_data in daily_logs_data:
            DailyLog.objects.create(
                trip=trip,
                day_number=log_data['day'],
                driving_hours=log_data['driving_hours'],
                off_duty_hours=log_data['off_duty_hours'],
                on_duty_hours=log_data['total_on_duty'],
                remarks='; '.join(log_data['remarks']),
                fueling_stop_details=log_data.get('fueling_stop_details', ''),
                stop_markers=json.dumps(log_data.get('stop_markers', []))
            )

        return JsonResponse({'message': 'Trip created successfully', 'trip_id': trip.id})

    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


# Generate PDF log
def generate_trip_pdf(request, trip_id):
    trip = Trip.objects.get(id=trip_id)
    daily_logs = trip.daily_logs.all()
    logs = [
        {
            'day': log.day_number,
            'driving_hours': log.driving_hours,
            'total_on_duty': log.on_duty_hours,
            'remarks': log.remarks.split('; ')
        }
        for log in daily_logs
    ]

    file_path = f'trip_{trip_id}_log.pdf'
    generate_pdf_log(logs, file_path)
    response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file_path}"'
    return response

# Generate Image log
def generate_trip_image(request, trip_id):
    trip = Trip.objects.get(id=trip_id)
    daily_logs = trip.daily_logs.all()
    logs = [
        {
            'day': log.day_number,
            'driving_hours': log.driving_hours,
            'total_on_duty': log.on_duty_hours,
            'remarks': log.remarks.split('; ')
        }
        for log in daily_logs
    ]

    file_path = f'trip_{trip_id}_log.png'
    generate_image_log(logs, file_path)
    response = FileResponse(open(file_path, 'rb'), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{file_path}"'
    return response

# ------------------------------
# New Expanded API Endpoints
# ------------------------------

# List Trips: Returns a list of trips with summary details
def list_trips(request):
    if request.method == 'GET':
        trips = Trip.objects.all().order_by('-created_at')
        trips_data = []
        for trip in trips:
            daily_logs = trip.daily_logs.all().order_by('day_number')
            logs_summary = []
            for log in daily_logs:
                logs_summary.append({
                    "day": log.day_number,
                    "driving_hours": log.driving_hours,
                    "on_duty_hours": log.on_duty_hours,
                    "remarks": log.remarks
                })
            trips_data.append({
                "id": trip.id,
                "current_location": trip.current_location,
                "pickup_location": trip.pickup_location,
                "dropoff_location": trip.dropoff_location,
                "distance": trip.distance,
                "route_polyline": trip.route_polyline,
                "daily_logs_summary": logs_summary,
            })
        return JsonResponse({"trips": trips_data})
    return JsonResponse({"error": "GET method required"}, status=405)

# Trip Detail: Returns all details for a specific trip
def trip_detail(request, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return JsonResponse({"error": "Trip not found"}, status=404)

    if request.method == 'GET':
        daily_logs = trip.daily_logs.all().order_by('day_number')
        logs = []
        for log in daily_logs:
            logs.append({
                "day": log.day_number,
                "driving_hours": log.driving_hours,
                "off_duty_hours": log.off_duty_hours,
                "on_duty_hours": log.on_duty_hours,
                "remarks": log.remarks
            })
        trip_data = {
            "id": trip.id,
            "current_location": trip.current_location,
            "pickup_location": trip.pickup_location,
            "dropoff_location": trip.dropoff_location,
            "distance": trip.distance,
            "hours_used": trip.hours_used,
            "departure_time": trip.departure_time.isoformat() if trip.departure_time else None,
            "route_polyline": trip.route_polyline,
            "daily_logs": logs,
        }
        return JsonResponse(trip_data)
    return JsonResponse({"error": "GET method required"}, status=405)


# Update Trip: Allow modifications to trip details
@csrf_exempt
def update_trip(request, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return JsonResponse({"error": "Trip not found"}, status=404)

    if request.method == 'PUT':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Update fields if provided in data
        if "current_location" in data:
            trip.current_location = data["current_location"]
        if "pickup_location" in data:
            trip.pickup_location = data["pickup_location"]
        if "dropoff_location" in data:
            trip.dropoff_location = data["dropoff_location"]
        if "hours_used" in data:
            trip.hours_used = data["hours_used"]
        if "departure_time" in data:
            from django.utils.dateparse import parse_datetime
            departure_time = parse_datetime(data["departure_time"])
            if departure_time:
                trip.departure_time = departure_time
        # Optionally, if address changes then you might re-fetch route info here
        trip.save()
        return JsonResponse({"message": "Trip updated successfully"})
    return JsonResponse({"error": "PUT method required"}, status=405)

# Delete Trip: Remove a trip
@csrf_exempt
def delete_trip(request, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return JsonResponse({"error": "Trip not found"}, status=404)

    if request.method == 'DELETE':
        trip.delete()
        return JsonResponse({"message": "Trip deleted successfully"})
    return JsonResponse({"error": "DELETE method required"}, status=405)

# Map Data API: Returns structured route information including stops and annotations
def trip_map_data(request, trip_id):
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return JsonResponse({"error": "Trip not found"}, status=404)

    if request.method == 'GET':
        # Get stored polyline as a string
        polyline = trip.route_polyline
        
        # Create stops array with pickup and dropoff locations
        stops = []
        
        # Get geocode for pickup location
        from .services import get_geocode
        pickup_coords = get_geocode(trip.pickup_location)
        if pickup_coords:
            stops.append({
                "lat": pickup_coords[0],
                "lng": pickup_coords[1],
                "location": f"Pickup: {trip.pickup_location}"
            })
        
        # Add stops from daily logs if they have coordinates
        daily_logs = trip.daily_logs.all().order_by('day_number')
        for log in daily_logs:
            try:
                if log.stop_markers:
                    markers = json.loads(log.stop_markers)
                    for marker in markers:
                        if 'lat' in marker and 'lng' in marker:
                            stops.append({
                                "lat": float(marker['lat']),
                                "lng": float(marker['lng']),
                                "location": f"Day {log.day_number} Stop"
                            })
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Get geocode for dropoff location
        dropoff_coords = get_geocode(trip.dropoff_location)
        if dropoff_coords:
            stops.append({
                "lat": dropoff_coords[0],
                "lng": dropoff_coords[1],
                "location": f"Dropoff: {trip.dropoff_location}"
            })
        
        # Return map data in the format expected by the frontend
        map_data = {
            "polyline": polyline,  # Pass the encoded polyline string directly
            "stops": stops
        }
        
        return JsonResponse(map_data)
    
    return JsonResponse({"error": "GET method required"}, status=405)


