import os

from oauth2client import service_account
from googleapiclient.discovery import build
from event import Event

GOOGLE_APPLICATION_CREDENTIALS = os.environ['GOOGLE_APPLICATION_CREDENTIALS']


def get_events(calendar_id, start_datetime, end_datetime):
    creds = service_account.ServiceAccountCredentials.from_json_keyfile_name(
        GOOGLE_APPLICATION_CREDENTIALS, "https://www.googleapis.com/auth/calendar.readonly"
    )
    service = build("calendar", "v3", credentials=creds)

    request = service.events().list(
        calendarId=calendar_id  # "r4uemkp00o4h6uoh38v8nuk8cg@group.calendar.google.com",
    )
    response = request.execute()
    events = Event.from_gcal_response(response)

    while "nextPageToken" in response:
        request = service.events().list_next(request, response)
        response = request.execute()
        events.extend(Event.from_gcal_response(response))
    return events
