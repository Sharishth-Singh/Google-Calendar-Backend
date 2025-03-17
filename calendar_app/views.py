import datetime
import random
import json
import os
import platform
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Set paths based on OS
if platform.system() == "Windows":  
    SERVICE_ACCOUNT_FILE = "calendar_project/credentials.json"
    EMOJIS_FILE = "calendar_project/emojis.json"
    KEYWORDS_FILE = "calendar_project/keywords.txt"
else:  
    SERVICE_ACCOUNT_FILE = "/home/Sharishth/Google-Calendar-Backend/calendar_project/credentials.json"
    EMOJIS_FILE = "/home/Sharishth/Google-Calendar-Backend/calendar_project/emojis.json"
    KEYWORDS_FILE = "/home/Sharishth/Google-Calendar-Backend/calendar_project/keywords.txt"

CALENDAR_ID = "sharishthsingh@gmail.com"


def authenticate_google_calendar():
    """Authenticate and return a Google Calendar service instance."""
    if not SERVICE_ACCOUNT_FILE:
        raise ValueError("Google service account credentials not found.")

    SCOPES = ['https://www.googleapis.com/auth/calendar']
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=credentials)


def get_today_events(service):
    """Fetch today's events from Google Calendar, excluding all-day events."""
    today = datetime.date.today().isoformat()

    # Define start and end time in IST
    today_min = f"{today}T00:00:00+05:30"  # 12:00 AM IST
    today_max = f"{today}T23:59:59+05:30"  # 11:59 PM IST

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=today_min,
        timeMax=today_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    # Filter out all-day events (which have "date" instead of "dateTime")
    filtered_events = [
        event for event in events_result.get('items', [])
        if "dateTime" in event["start"]  # Keeps only timed events
    ]

    return filtered_events



def get_random_emoji(slot_name):
    """Fetch a random emoji based on slot name."""
    with open(EMOJIS_FILE, "r", encoding="utf-8") as file:
        emoji_data = json.load(file)

    slot_name_lower = slot_name.lower()
    for entry in emoji_data:
        if any(keyword in slot_name_lower for keyword in entry["keywords"]):
            return entry["emoji"]

    default_entry = next((e for e in emoji_data if "default" in e["keywords"]), None)
    return random.choice(default_entry["emoji"]) if default_entry else "❓"

def format_duration(start_time, end_time):
    # Correct format for 12-hour time with AM/PM
    fmt = "%I:%M %p"
    start = datetime.datetime.strptime(start_time, fmt)
    end = datetime.datetime.strptime(end_time, fmt)

    # Calculate duration
    duration = end - start
    hours, minutes = divmod(duration.seconds // 60, 60)

    # Format output
    if hours == 0:
        return f"{minutes} m"
    elif minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {minutes} m"



def create_event(service, start_date, start_time, end_time, slot_name):
    """Create an event in Google Calendar."""
    if not CALENDAR_ID:
        raise ValueError("Google Calendar ID is missing.")

    emoji = get_random_emoji(slot_name)

    # slot_name_with_emoji = f"{slot_name} {emoji}"  
    slot_name_with_emoji = f"{slot_name}{emoji}({format_duration(start_time, end_time)})"
    print(slot_name_with_emoji)
    # Set colorId based on slot_name
    cId = 5
    with open(KEYWORDS_FILE, "r") as file:
        keywords = [line.strip().lower() for line in file]

    if any(keyword in slot_name.lower() for keyword in keywords):
        cId = 4
    elif "class" in slot_name.lower() and "note" not in slot_name.lower() and "revision" not in slot_name.lower():
        cId = 2
    elif "psir" not in slot_name.lower() and "political science and international relation" not in slot_name.lower():
        cId = None

    try:
        # Convert time to 24-hour format
        start_time_24 = datetime.datetime.strptime(start_time, '%I:%M %p').strftime('%H:%M')
        end_time_24 = datetime.datetime.strptime(end_time, '%I:%M %p').strftime('%H:%M')
    except ValueError:
        return None

    start_datetime = f"{start_date}T{start_time_24}:00+05:30"
    end_datetime = f"{start_date}T{end_time_24}:00+05:30"

    event = {
        'summary': slot_name_with_emoji,
        'start': {'dateTime': start_datetime, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_datetime, 'timeZone': 'Asia/Kolkata'},
        'transparency': 'transparent',
        'colorId': cId,
        'reminders': {
            'useDefault': False,
            'overrides': [{'method': 'popup', 'minutes': 2}],
        },
    }

    # Create event in Google Calendar
    try:
        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return event.get('htmlLink')
    except Exception:
        return None


@csrf_exempt
def add_events(request):
    """Django view to add events to Google Calendar."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            time_slot_lines = data.get("time_slots", [])

            service = authenticate_google_calendar()
            existing_events = {event['summary'] for event in get_today_events(service)}

            event_date = datetime.date.today().isoformat()
            created_events = []

            for line in time_slot_lines:
                if 'next day;' in line.lower():
                    event_date = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
                    continue

                time_slot = line.split('=')
                if len(time_slot) == 2:
                    time_range, slot_name = time_slot[0].strip(), time_slot[1].strip()
                    start_time, end_time = map(str.strip, time_range.split('-'))

                    if slot_name in existing_events:
                        continue

                    event_url = create_event(service, event_date, start_time, end_time, slot_name)
                    if event_url:
                        created_events.append({'title': slot_name, 'event_url': event_url})

            return JsonResponse({"status": "success", "created_events": created_events}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


def get_events(request):
    """Django view to fetch today's events."""
    if request.method == 'GET':
        try:
            service = authenticate_google_calendar()
            today_events = get_today_events(service)

            formatted_events = [
                {
                    "title": event["summary"],
                    "start": event["start"].get("dateTime", event["start"].get("date")),  # Handle both date and dateTime
                    "end": event["end"].get("dateTime", event["end"].get("date"))  # Handle both date and dateTime
                }
                for event in today_events
            ]


            return JsonResponse({"status": "success", "events": formatted_events}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


def home(request):
    """Home page response."""
    return HttpResponse("Welcome to the Calendar App!")
