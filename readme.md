# 📅 Django Project Documentation

## Overview
This Django project integrates with Google Calendar to manage events. It provides APIs for:
- Fetching today's events from Google Calendar.
- Adding new events to Google Calendar.
- Reading and updating a local `events.txt` file.

---

## Project Structure

```
calendar_project/
│── calendar_app/
│   ├── views.py      # Handles API logic
│   ├── urls.py       # Defines API routes
│── urls.py           # Main project URL configuration
│── settings.py       # (Not provided, assumed to contain project settings)
```

---

## Dependencies
Ensure you have the following installed:
```sh
pip install django google-auth google-auth-oauthlib google-auth-httplib2 googleapiclient python-dotenv python-dateutil
```

---

## URL Configuration

### **1. Project-wide URLs (`calendar_project/urls.py`)**
Includes app URLs:
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('calendar_app.urls')),
]
```

### **2. App-specific URLs (`calendar_app/urls.py`)**
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add-events/', views.add_events, name='add_events'),
    path('get_events/', views.get_events, name='get_events'),
    path('get-file-content/', views.get_file_content, name='get_file_content'),
    path('update-file-content/', views.update_file_content, name='update_file_content'),
]
```

---

## Views (`views.py`)

### **1. Google Calendar Integration**
#### `authenticate_google_calendar()`
- Loads `credentials.json` and authenticates Google Calendar API.
- Returns a service instance to interact with the calendar.

#### `get_today_events(service)`
- Fetches today's events (or yesterday’s if today is empty).
- Ignores all-day events.
- If any event contains "morning," shifts all events to tomorrow.

#### `create_event(service, start_date, start_time, end_time, slot_name)`
- Adds an event with:
  - **Emoji-based categorization** (based on keywords in `emojis.json`).
  - **Color coding** (based on event type in `keywords.txt`).
- Uses `Asia/Kolkata` timezone.

---

### **2. Event Management**
#### `add_events(request)`
- **Method:** `POST`
- **Request Body:** JSON with `time_slots` (list of time slots in `"HH:MM AM/PM = Event Name"` format).
- **Working:**
  1. Authenticates with Google Calendar.
  2. Checks existing events to avoid duplicates.
  3. Creates and adds new events if they don’t exist.
- **Response:** Returns created event details with Google Calendar links.

#### `get_events(request)`
- **Method:** `GET`
- **Working:**
  1. Fetches today’s events from Google Calendar.
  2. Formats event details (`title`, `start`, `end`).
- **Response:** Returns list of today’s events.

---

### **3. File Operations**
#### `get_file_content(request)`
- **Method:** `GET`
- **Working:** Reads `events.txt` and returns its content.

#### `update_file_content(request)`
- **Method:** `POST`
- **Request Body:** Raw text to overwrite `events.txt`.
- **Working:** Saves new content to the file.

---

### **4. Miscellaneous**
#### `home(request)`
- **Method:** `GET`
- **Working:** Returns `"Welcome to the Calendar App!"` as a response.

---

## Working & Usage

### **1. Run the Django Server**
```sh
python manage.py runserver
```

### **2. Access API Endpoints**
| Endpoint                  | Method | Description |
|---------------------------|--------|-------------|
| `/`                       | GET    | Returns a welcome message |
| `/get_events/`            | GET    | Fetches today's events from Google Calendar |
| `/add-events/`            | POST   | Adds events to Google Calendar |
| `/get-file-content/`      | GET    | Reads `events.txt` content |
| `/update-file-content/`   | POST   | Updates `events.txt` content |

#### Example: **Adding Events**
```json
POST /add-events/
{
    "time_slots": [
        "09:00 AM - 10:00 AM = Study",
        "11:00 AM - 12:00 PM = Meeting"
    ]
}
```
**Response:**
```json
{
    "status": "success",
    "created_events": [
        {"title": "Study 📚", "event_url": "https://calendar.google.com/event?eid=xyz"},
        {"title": "Meeting 💼", "event_url": "https://calendar.google.com/event?eid=abc"}
    ]
}
```

---