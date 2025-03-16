# Trucking HOS (Hours of Service) Trip Planner

## Project Overview
This Django application helps truck drivers plan their trips while adhering to Federal Motor Carrier Safety Administration (FMCSA) Hours of Service (HOS) regulations. The system calculates daily driving logs based on trip distance, current hours used, and departure time, ensuring compliance with maximum driving hours, required rest breaks, and cumulative hour limits.

## Features
- **Trip Planning**: Create trips with pickup and dropoff locations
- **Route Calculation**: Automatically calculates routes and distances using OpenRouteService API
- **HOS Compliance**: Enforces FMCSA regulations:
  - 11-hour daily driving limit
  - 14-hour on-duty limit
  - 10-hour off-duty requirement
  - 8-hour driving limit before required rest break
  - 70-hour cumulative limit with 34-hour reset option
- **Daily Log Generation**: Creates detailed logs for each day of the trip
- **Fueling Stop Planning**: Automatically schedules fueling stops every 1,000 miles
- **PDF & Image Export**: Generate visual reports of daily logs
- **Interactive Map**: View the trip route with annotated stops

## Technical Architecture
- **Backend**: Django framework
- **Mapping**: OpenRouteService API for geocoding and route calculation
- **Document Generation**: ReportLab for PDF creation, PIL for image generation
- **Data Storage**: Django ORM with SQLite/PostgreSQL

## Installation

### Prerequisites
- Python 3.8+
- Django 3.2+
- Required Python packages (see requirements below)

### Setup
1. Clone the repository:
   ```
   git clone https://github.com/MohammadHamza11/ELD_Project-planner.git
   cd ELD_Project-planner
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Start the development server:
   ```
   python manage.py runserver
   ```

## Requirements
- Django
- requests
- reportlab
- Pillow
- googlemaps (optional)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/trips/` | GET | List all trips |
| `/trips/create/` | POST | Create a new trip |
| `/trips/<trip_id>/` | GET | Get trip details |
| `/trips/<trip_id>/update/` | PUT | Update trip details |
| `/trips/<trip_id>/delete/` | DELETE | Delete a trip |
| `/trips/<trip_id>/pdf/` | GET | Generate PDF log |
| `/trips/<trip_id>/image/` | GET | Generate image log |
| `/trips/<trip_id>/map/` | GET | Get map data for trip visualization |

## Example Usage

### Creating a Trip
```json
POST /trips/create/
{
  "current_location": "Chicago, IL",
  "pickup_location": "Denver, CO",
  "dropoff_location": "Los Angeles, CA",
  "hours_used": 0,
  "departure_time": "2025-03-16T08:00"
}
```

## FMCSA Compliance
This application helps drivers comply with FMCSA regulations but should be used as a planning tool only. Drivers are responsible for maintaining accurate logs according to current regulations.

## License
MIT License

## Contributing
Contributions welcome! Please feel free to submit a Pull Request.
