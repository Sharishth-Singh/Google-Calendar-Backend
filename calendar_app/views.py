import datetime
import random
import json
import os
import platform
import subprocess
import requests
import re
from calendar_project.questions import get_pwonlyias_questions_by_date
from lxml import etree
from io import StringIO
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv


# Load environment variables
load_dotenv()
import os
import time

# Set the timezone to India (Asia/Kolkata)
os.environ["TZ"] = "Asia/Kolkata"
# time.tzset()

# Now, any time-related functions will use the India timezone.
# For example:

import datetime
today_india = datetime.datetime.now()
print(f"Current time in India: {today_india}")

#To verify:
print(time.strftime('%Z %z'))

# Set paths based on OS
if platform.system() == "Windows":  
    SERVICE_ACCOUNT_FILE = "calendar_project/credentials.json"
    EMOJIS_FILE = "calendar_project/emojis.json"
    KEYWORDS_FILE = "calendar_project/keywords.txt"
    BASE_DIR = "calendar_project"
else:  
    SERVICE_ACCOUNT_FILE = "/home/Sharishth/Google-Calendar-Backend/calendar_project/credentials.json"
    EMOJIS_FILE = "/home/Sharishth/Google-Calendar-Backend/calendar_project/emojis.json"
    KEYWORDS_FILE = "/home/Sharishth/Google-Calendar-Backend/calendar_project/keywords.txt"
    BASE_DIR = "/home/Sharishth/Google-Calendar-Backend/calendar_project"


CALENDAR_ID = "sharishthsingh@gmail.com"


def authenticate_google_calendar():
    """Authenticate and return a Google Calendar service instance."""
    if not SERVICE_ACCOUNT_FILE:
        raise ValueError("Google service account credentials not found.")

    SCOPES = ['https://www.googleapis.com/auth/calendar']
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=credentials)


import datetime
from dateutil.parser import parse
from dateutil.tz import tzlocal
def get_today_events(service):
    """Fetch today's events from Google Calendar, excluding all-day events.
       If no timed events exist, fetch yesterday's events.
       If any event contains 'morning', shift all events to tomorrow.
    """
    def fetch_events(date):
        """Helper function to fetch events for a given date."""
        date_min = f"{date.isoformat()}T00:00:00+05:30"
        date_max = f"{date.isoformat()}T23:59:59+05:30"
        
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=date_min,
            timeMax=date_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])

    today = datetime.date.today()
    events = fetch_events(today)

    # Filter out all-day events
    filtered_events = [event for event in events if "dateTime" in event["start"]]

    # If no timed events, fetch yesterday's events
    if not filtered_events:
        yesterday = today - datetime.timedelta(days=1)
        events = fetch_events(yesterday)
        filtered_events = [event for event in events if "dateTime" in event["start"]]

    # Check if any event contains "morning"
    contains_morning = any("morning" in event.get("summary", "").lower() for event in filtered_events)
    print("container: ",contains_morning)
    # If "morning" exists, shift all events to tomorrow
    if contains_morning:
        global new_date
        new_date = today + datetime.timedelta(days=1)

        for event in filtered_events:
            start_time = parse(event["start"]["dateTime"])
            end_time = parse(event["end"]["dateTime"])

            event["start"]["dateTime"] = (start_time + datetime.timedelta(days=1)).isoformat()
            event["end"]["dateTime"] = (end_time + datetime.timedelta(days=1)).isoformat()

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

@csrf_exempt
def fetch_pwonlyias_questions(today=None):
    question = get_pwonlyias_questions_by_date()
    return JsonResponse({"questions": "\n\n".join(question)})


@csrf_exempt
def fetch_github_api_data(request):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "application/vnd.github.v3+json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Upgrade-Insecure-Requests": "1"
    }

    # Optional: get username from query ?user=octocat
    github_user = request.GET.get("user", "octocat")
    url = f"https://api.github.com/users/{github_user}"

    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses
        data = response.json()

        return JsonResponse({
            "fetched_at": str(datetime.datetime.now()),
            "user": github_user,
            "data": data
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
def create_event(service, start_date, start_time, end_time, slot_name):
    """Create an event in Google Calendar."""
    if not CALENDAR_ID:
        raise ValueError("Google Calendar ID is missing.")

    emoji = get_random_emoji(slot_name)

    # slot_name_with_emoji = f"{slot_name} {emoji}"  
    slot_name_with_emoji = f"{slot_name}{emoji}({format_duration(start_time, end_time)})"
    # Set colorId based on slot_name
    cId = 5
    with open(KEYWORDS_FILE, "r") as file:
        keywords = [line.strip().lower() for line in file]

    if any(keyword in slot_name.lower() for keyword in keywords):
        cId = 4
    elif "class" in slot_name.lower() and "note" not in slot_name.lower() and "revision" not in slot_name.lower():
        cId = 2
    elif "psir" not in slot_name.lower() and "political science and international relation" not in slot_name.lower() and "political science & international relation" not in slot_name.lower():
        cId = None

    try:
        # Convert time to 24-hour format
        start_time_24 = datetime.datetime.strptime(start_time, '%I:%M %p').strftime('%H:%M')
        end_time_24 = datetime.datetime.strptime(end_time, '%I:%M %p').strftime('%H:%M')
    except ValueError:
        return None

    start_datetime = f"{start_date}T{start_time_24}:00+05:30"
    end_datetime = f"{start_date}T{end_time_24}:00+05:30"

    description = None
    if("editorial" in slot_name.lower()):
        try:
            description = "\n\n".join(get_pwonlyias_questions_by_date())  # Join the questions into a single string
        except:
            description = "Unable to fetch questions."


    event = {
        'summary': slot_name_with_emoji,
        'description': description,
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
            print(data)
            time_slot_lines = data.get("time_slots", [])

            service = authenticate_google_calendar()
            existing_events = {event['summary'] for event in get_today_events(service)}

            event_date = new_date
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


def get_file_content(request):
    """Read and return the content of a .txt file based on filename query param."""
    if request.method == 'GET':
        filename = request.GET.get('filename')
        if not filename:
            return HttpResponse("Filename not provided.", content_type="text/plain", status=400)

        file_path = os.path.join(BASE_DIR, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            return HttpResponse(content, content_type="text/plain", status=200)
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", content_type="text/plain", status=400)

    return HttpResponse("Invalid request method.", content_type="text/plain", status=405)


@csrf_exempt
def update_file_content(request):
    """Overwrite a .txt file with new content based on filename query param."""
    if request.method == 'POST':
        filename = request.GET.get('filename')
        if not filename:
            return HttpResponse("Filename not provided.", content_type="text/plain", status=400)

        file_path = os.path.join(BASE_DIR, filename)
        try:
            new_content = request.body.decode("utf-8")  # Read raw text

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(new_content)  # Overwrite file

            return HttpResponse("File updated successfully.", content_type="text/plain", status=200)
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}", content_type="text/plain", status=400)

    return HttpResponse("Invalid request method.", content_type="text/plain", status=405)


def home(request):
    """Home page response."""
    return HttpResponse("Welcome to the Calendar App!")
