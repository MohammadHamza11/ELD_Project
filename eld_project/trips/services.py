# trips/services.py
import requests

OPENROUTESERVICE_API_KEY = '5b3ce3597851110001cf624829a1a42d8e464d0ca2641e69ea2ef3d3'

def get_geocode(address):
    url = 'https://api.openrouteservice.org/geocode/search'
    params = {
        'api_key': OPENROUTESERVICE_API_KEY,
        'text': address,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get('features'):
            # OpenRouteService returns [lon, lat]; we swap to (lat, lon)
            coords = data['features'][0]['geometry']['coordinates']
            return coords[1], coords[0]
    return None

def get_route(start_address, end_address):
    start_coords = get_geocode(start_address)  # returns (lat, lon)
    end_coords = get_geocode(end_address)      # returns (lat, lon)

    if not start_coords or not end_coords:
        return None

    url = 'https://api.openrouteservice.org/v2/directions/driving-car'
    headers = {
        'Authorization': OPENROUTESERVICE_API_KEY,
        'Content-Type': 'application/json'
    }
    body = {
        'coordinates': [
            [start_coords[1], start_coords[0]],  # [lon, lat]
            [end_coords[1], end_coords[0]]       # [lon, lat]
        ],
        'geometry': True  # Correct way to request geometry data
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        data = response.json()
        
        # Check if "routes" is in the data
        if 'routes' in data and len(data['routes']) > 0:
            route = data['routes'][0]
            distance_meters = route['summary']['distance']  # in meters
            duration_seconds = route['summary']['duration']  # in seconds
            geometry = route.get('geometry')  # This should be the encoded polyline string
            
            # Convert distance to miles, duration to hours
            distance_miles = distance_meters / 1609.34
            duration_hours = duration_seconds / 3600

            return {
                'distance': distance_miles,
                'duration': duration_hours,
                'geometry': geometry
            }
        else:
            print("No 'routes' key or empty routes array in the response.")
            return None
    else:
        print("Directions request failed with status code:", response.status_code)
        print("Response:", response.text)
        return None
    
    