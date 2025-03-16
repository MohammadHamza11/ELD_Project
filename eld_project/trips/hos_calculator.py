from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont

MAX_DRIVING_HOURS = 11
MAX_ON_DUTY_HOURS = 14
MIN_OFF_DUTY_HOURS = 10
MAX_CUMULATIVE_HOURS = 70
REST_BREAK_REQUIRED_AFTER_HOURS = 8

def generate_pdf_log(daily_logs, file_path):
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    c.drawString(30, height - 50, 'FMCSA Daily Log')

    y = height - 100
    for log in daily_logs:
        c.drawString(30, y, f"Day {log['day']}: Driving Hours: {log['driving_hours']}, On-Duty Hours: {log['total_on_duty']}")
        c.drawString(30, y - 15, f"Remarks: {'; '.join(log['remarks'])}")
        y -= 40

    c.save()

def generate_image_log(daily_logs, file_path):
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    y = 20
    draw.text((20, y), 'FMCSA Daily Log', fill=(0, 0, 0), font=font)
    y += 30

    for log in daily_logs:
        draw.text((20, y), f"Day {log['day']}: Driving: {log['driving_hours']} hrs, On-Duty: {log['total_on_duty']} hrs", fill=(0, 0, 0), font=font)
        draw.text((20, y + 15), f"Remarks: {'; '.join(log['remarks'])}", fill=(0, 0, 0), font=font)
        y += 40

    img.save(file_path)

def calculate_daily_logs(trip_distance, hours_used, departure_time):
    daily_logs = []
    remaining_distance = trip_distance
    day = 1
    avg_speed = 55

    # Use departure_time (if provided) as the start time; otherwise default to now
    current_time = departure_time if departure_time else datetime.now()

    cumulative_hours = 0
    last_break_time = 0
    distance_since_fuel = 0  # Track miles since last fueling stop

    while remaining_distance > 0:
        log = {
            'day': day,
            'driving_hours': 0,
            'off_duty_hours': 0,
            'total_on_duty': 0,
            'remarks': [],
            'stop_markers': []  # Detailed markers for events
        }
        available_hours = MAX_ON_DUTY_HOURS
        driving_hours = 0

        # Record the start-of-day marker
        log['stop_markers'].append({'type': 'day_start', 'time': current_time.isoformat()})

        if day == 1:
            # Account for pickup (assume 1 hour pickup)
            available_hours -= 1
            log['remarks'].append("1 hour pickup")
            current_time += timedelta(hours=1)
            log['stop_markers'].append({'type': 'pickup', 'time': current_time.isoformat()})

        # Process the driving segments for the day
        while available_hours > 0 and remaining_distance > 0:
            # Insert a rest break if needed
            if driving_hours >= REST_BREAK_REQUIRED_AFTER_HOURS and last_break_time >= 8:
                available_hours -= 0.5
                last_break_time = 0
                log['remarks'].append("30-minute rest break")
                current_time += timedelta(hours=0.5)
                log['stop_markers'].append({'type': 'rest_break', 'time': current_time.isoformat()})
                continue

            # Edge case: adjust driving if cumulative hours are nearing the 70-hour limit
            remaining_cumulative = MAX_CUMULATIVE_HOURS - cumulative_hours
            max_possible_drive = min(available_hours, remaining_distance / avg_speed, remaining_cumulative)
            if max_possible_drive <= 0:
                log['remarks'].append("Cumulative hours near threshold; ending day early")
                break

            potential_distance = max_possible_drive * avg_speed

            # Check if the next segment would exceed the 1,000-mile fueling threshold
            if distance_since_fuel + potential_distance >= 1000:
                hours_to_fuel = (1000 - distance_since_fuel) / avg_speed
                hours_to_fuel = min(hours_to_fuel, available_hours, MAX_DRIVING_HOURS - driving_hours)
                if hours_to_fuel > 0:
                    # Drive only up to the fueling threshold
                    driving_hours += hours_to_fuel
                    available_hours -= hours_to_fuel
                    driven_distance = hours_to_fuel * avg_speed
                    remaining_distance -= driven_distance
                    last_break_time += hours_to_fuel
                    cumulative_hours += hours_to_fuel
                    distance_since_fuel += driven_distance
                    log['remarks'].append("Fueling stop")
                    log['fueling_stop_details'] = "Fueling stop at 1,000 miles threshold"
                    current_time += timedelta(hours=hours_to_fuel)
                    log['stop_markers'].append({'type': 'fueling_stop', 'time': current_time.isoformat()})
                    distance_since_fuel = 0  # Reset fueling counter
                    continue

            # Normal driving segment
            if driving_hours + max_possible_drive <= MAX_DRIVING_HOURS:
                driving_hours += max_possible_drive
                available_hours -= max_possible_drive
                driven_distance = max_possible_drive * avg_speed
                remaining_distance -= driven_distance
                distance_since_fuel += driven_distance
                last_break_time += max_possible_drive
                cumulative_hours += max_possible_drive
                current_time += timedelta(hours=max_possible_drive)
                # Record the driving segment marker (optionally including duration)
                log['stop_markers'].append({
                    'type': 'driving_segment',
                    'time': current_time.isoformat(),
                    'duration': max_possible_drive
                })
            else:
                break

            # If the trip ends mid-day, mark it
            if remaining_distance <= 0:
                log['remarks'].append("Trip ended mid-day")
                log['stop_markers'].append({'type': 'trip_end', 'time': current_time.isoformat()})
                break

        log['driving_hours'] = driving_hours
        log['total_on_duty'] = MAX_ON_DUTY_HOURS - available_hours
        log['off_duty_hours'] = MIN_OFF_DUTY_HOURS

        if remaining_distance <= 0:
            # Add drop-off if the trip has finished
            log['total_on_duty'] += 1
            log['remarks'].append("1 hour drop-off")
            current_time += timedelta(hours=1)
            log['stop_markers'].append({'type': 'drop_off', 'time': current_time.isoformat()})

        daily_logs.append(log)
        day += 1

        # End-of-day off-duty period and cumulative update
        cumulative_hours += MIN_OFF_DUTY_HOURS
        current_time += timedelta(hours=MIN_OFF_DUTY_HOURS)

        if cumulative_hours >= MAX_CUMULATIVE_HOURS:
            log['remarks'].append("34-hour reset applied")
            cumulative_hours = 0
            current_time += timedelta(hours=34)
            log['stop_markers'].append({'type': 'reset', 'time': current_time.isoformat()})

    return daily_logs
