import sys
import datetime
import random
import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from django.http import HttpResponse
import platform

# Load environment variables
load_dotenv()

# Get credentials path & calendar ID from .env
if platform.system() == "Windows":  # Linux (PythonAnywhere)
    SERVICE_ACCOUNT_FILE = "calendar_project/credentials.json"
else:  # Windows / Localhost
    SERVICE_ACCOUNT_FILE = "/home/Sharishth/Google-Calendar-Backend/calendar_project/credentials.json"
# SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS_PATH")
CALENDAR_ID = "sharishthsingh@gmail.com"


def get_random_emoji(slot_name, json_file="calendar_project/emojis.json"):
    """Fetch a random emoji based on slot name."""
    with open(json_file, "r", encoding="utf-8") as file:
        emoji_data = json.load(file)

    slot_name_lower = slot_name.lower()
    for entry in emoji_data:
        if any(keyword in slot_name_lower for keyword in entry["keywords"]):
            return entry["emoji"]

    default_entry = next((e for e in emoji_data if "default" in e["keywords"]), None)
    return random.choice(default_entry["emoji"]) if default_entry else "❓"


def authenticate_google_calendar():
    """Authenticate and return a Google Calendar service instance."""
    if not SERVICE_ACCOUNT_FILE:
        raise ValueError("Google service account credentials not found.")

    SCOPES = ['https://www.googleapis.com/auth/calendar']
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=credentials)


def create_event(service, start_date, start_time, end_time, slot_name):
    """Create an event in Google Calendar."""
    if not CALENDAR_ID:
        raise ValueError("Google Calendar ID is missing.")

    emoji = get_random_emoji(slot_name)
    slot_name_with_emoji = f"{slot_name} {emoji}"

    # Set colorId based on slot_name
    cId = 5
    with open("calendar_project/keywords.txt", "r") as file:
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

            # Get today's events to avoid duplicates
            today_events = service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=datetime.datetime.utcnow().isoformat() + 'Z',
                timeMax=(datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            existing_events = {event['summary'] for event in today_events.get('items', [])}

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

def home(request):
    return HttpResponse("Welcome to the Calendar App!")
