from __future__ import print_function

import datetime
import pathlib
import time

from . import googleapi

LOCAL_TIMEZONE = "Europe/Prague"


def now():
    return datetime.datetime.now()


def list_events(calendar="primary", date=None, max_results=10, force_day=True):
    if not date:
        date = now()
    date = todt(date)
    date = todt(date.date())
    if force_day:
        timeMax = get_google_from_dt(date + datetime.timedelta(days=1)) + "Z"
    else:
        timeMax = None
    date = get_google_from_dt(date) + "Z"

    return service.events().list(
        calendarId=calendar, timeMin=date,
        maxResults=max_results, singleEvents=True,
        orderBy="startTime", timeMax=timeMax,
    ).execute()["items"]


def get_utc_offset():
    now_timestamp = time.time()
    return datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)


def get_time(event):
    return [get_dt_from_google(event["start"]), get_dt_from_google(event["end"])]


def get_timestamp(event):
    return [x.timestamp() for x in get_time(event)]


def todt(dt):
    if not isinstance(dt, datetime.datetime):
        if isinstance(dt, datetime.date):
            dt = datetime.datetime.combine(dt, datetime.datetime.min.time())
        elif isinstance(dt, datetime.time):
            dt = datetime.datetime.combine(datetime.date.today(), dt)
    return dt


def get_current_events(date=None):
    if date is None:
        date = now()
    return [event for event in list_events(date=date) if get_time(event)[0] <= now() <= get_time(event)[1]]


def get_google_from_dt(dt):
    dt = todt(dt)
    return dt.isoformat()


def get_dt_from_google(dt):
    form = '%Y-%m-%dT%H:%M:%S%z'
    dif = datetime.timedelta(days=0)
    if isinstance(dt, dict):
        if "timeZone" in dt.keys():
            if dt["timeZone"] != LOCAL_TIMEZONE:
                dif = get_utc_offset()
        if "dateTime" in dt.keys():
            dt = dt["dateTime"]
        else:
            dt = dt["date"]; form = "%Y-%m-%d"
    return datetime.datetime.strptime(dt, form).replace(tzinfo=None) + dif


def create_event(
        name, start, end=None, description=None, location=None,
        color=None, all_day=False, calendar_id='primary'
):
    """
    COLORS
    1 blue
    2 green
    3 purple
    4 red
    5 yellow
    6 orange
    7 turquoise
    8 gray
    9 bold blue
    10 bold green
    11 bold red
    """
    if not end:
        end = start + datetime.timedelta(hours=1)
    event = {
        'summary': name,
        'start': {'dateTime': get_google_from_dt(start), "timeZone": LOCAL_TIMEZONE},
        'end': {'dateTime': get_google_from_dt(end), "timeZone": LOCAL_TIMEZONE},
    }
    if all_day:
        event["start"] = datetime.datetime.strftime(todt(start), "%Y-%m-%d")
        event["end"] = datetime.datetime.strftime(todt(end), "%Y-%m-%d")
    if description:
        event["description"] = description
    if location:
        event["location"] = location
    if color:
        event["colorId"] = str(color)

    return service.events().insert(calendarId=calendar_id, body=event).execute()


def import_from_ics(file_name):
    file_name = pathlib.Path(file_name).expanduser()
    if file_name.exists():
        with open(file_name, "r") as f:
            content = f.read().split("\n")

        event = {}
        for line in content:
            if line == "BEGIN:VEVENT":
                event = {}
            if line.startswith("DTSTART:"):
                event["start"] = datetime.datetime.strptime(line.split(":", 1)[1], "%Y%m%dT%H%M%S%z")
            if line.startswith("DTEND:"):
                event["end"] = datetime.datetime.strptime(line.split(":", 1)[1], "%Y%m%dT%H%M%S%z")
            if line.startswith("SUMMARY:"):
                event["sum"] = line.split(":", 1)[1]
            if line.startswith("DESCRIPTION:"):
                event["des"] = line.split(":", 1)[1].replace("\\n", "\n")
            if line == "END:VEVENT":
                create_event(event["sum"], event["start"], event["end"], event["des"])
            print(event)


service = googleapi.get_service('calendar')
