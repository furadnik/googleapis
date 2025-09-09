"""Calendar api."""
from __future__ import annotations, print_function

import datetime
import pathlib
import time
from dataclasses import dataclass
from enum import StrEnum
from functools import partial
from subprocess import PIPE, Popen
from typing import Iterable, Iterator, Optional, Union

import pytz

from . import googleapi


def get_timezone() -> str:
    """Get current timezone."""
    return Popen("timedatectl show | grep 'Timezone=' | cut -d= -f2", shell=True, stdout=PIPE  # nosec
                 ).stdout.read().decode().strip() or "Europe/Prague"  # type: ignore


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

    return service().events().list(
        calendarId=calendar, timeMin=date,
        maxResults=max_results, singleEvents=True,
        orderBy="startTime", timeMax=timeMax,
    ).execute()["items"]


def get_utc_offset():
    now_timestamp = time.time()
    return datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)


def get_time(event):
    return [strip_timezone(get_dt_from_google(event["start"])), strip_timezone(get_dt_from_google(event["end"]))]


def get_timestamp(event):
    return [x.timestamp() for x in get_time(event)]


def todt(dt: datetime.datetime | datetime.date | datetime.time) -> datetime.datetime:
    if not isinstance(dt, datetime.datetime):
        if isinstance(dt, datetime.date):
            dt = datetime.datetime.combine(dt, datetime.datetime.min.time())
        elif isinstance(dt, datetime.time):
            dt = datetime.datetime.combine(datetime.date.today(), dt)
    return dt


def get_current_events(date=None):
    if date is None:
        date = now()
    return [event for event in list_events(date=date) if get_time(event)[0] <= date <= get_time(event)[1]]


def get_google_from_dt(dt):
    dt = todt(dt)
    return dt.isoformat()


def get_dt_from_google(dt):
    if isinstance(dt, dict):
        if "dateTime" in dt.keys():
            form = '%Y-%m-%dT%H:%M:%S%z'
            dt = dt["dateTime"]
        else:
            dt = dt["date"]
            form = "%Y-%m-%d"
    return datetime.datetime.strptime(dt, form)


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
    tz = get_timezone()
    if not end:
        end = start + datetime.timedelta(hours=1)
    event = {
        'summary': name,
        'start': {'dateTime': get_google_from_dt(start), "timeZone": tz},
        'end': {'dateTime': get_google_from_dt(end), "timeZone": tz},
    }
    if all_day:
        event["start"] = {"date": datetime.datetime.strftime(todt(start), "%Y-%m-%d")}
        event["end"] = {"date": datetime.datetime.strftime(todt(end), "%Y-%m-%d")}
    if description:
        event["description"] = description
    if location:
        event["location"] = location
    if color:
        event["colorId"] = str(color)

    return service().events().insert(calendarId=calendar_id, body=event).execute()


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


def strip_timezone(aware: datetime.datetime) -> datetime.datetime:
    """Strip timezone from dt."""
    tz = get_timezone()
    local = aware.astimezone(pytz.timezone(tz))
    return local.replace(tzinfo=None)


service = googleapi.Service('calendar')


@dataclass
class Calendar:
    """Google Calendar repr."""

    calendar_id: str = 'primary'
    service: googleapi.Service = service

    def __repr__(self) -> str:
        """Repr cal."""
        return f"Calendar({self.calendar_id})"

    def create_event(self, name: str,
                     start: datetime.datetime | datetime.date, end: datetime.datetime | datetime.date | None = None,
                     description: Optional[str] = None, location: Optional[str] = None,
                     color: Union[str, int, None] = None, all_day: bool | None = None
                     ) -> Event:
        """Create a Calendar Event."""
        tz = get_timezone()
        if not end:
            end = start + datetime.timedelta(hours=1)
        event = {
            'summary': name,
            'start': {'dateTime': get_google_from_dt(start), "timeZone": tz},
            'end': {'dateTime': get_google_from_dt(end), "timeZone": tz},
        }
        # by default: date = all day & datetime = not all day
        if all_day is None:
            all_day = not isinstance(start, datetime.datetime)
        if all_day:
            event["start"] = {"date": datetime.datetime.strftime(todt(start), "%Y-%m-%d")}
            event["end"] = {"date": datetime.datetime.strftime(todt(end), "%Y-%m-%d")}
        if description:
            event["description"] = description
        if location:
            event["location"] = location
        if color:
            event["colorId"] = str(color)

        response = service().events().insert(calendarId=self.calendar_id,
                                             body=event).execute()
        return Event.from_service_event(self, response)

    def list_events(self, date=None, max_results=50, force_day=True, future=False, past=False,
                    by_me: bool | None = None) -> Iterator[Event]:
        """Get events.

        by_me restricts to only events by me (True), or not by me (False). If None, no restriction is applied.
        """
        if not date:
            date = now()
        date = todt(date)
        date = todt(date.date())
        if force_day:
            timeMax = get_google_from_dt(date + datetime.timedelta(days=1)) + "Z"
        else:
            timeMax = None
        date = get_google_from_dt(date) + "Z"

        response = service().events().list(
            calendarId=self.calendar_id, timeMin=date,
            maxResults=max_results, singleEvents=True,
            orderBy="startTime", timeMax=timeMax
        ).execute()["items"]

        events: Iterator[Event] = map(partial(Event.from_service_event, self),
                                      response)

        if future:
            events = filter(lambda x: x.start >= datetime.datetime.now(),
                            events)

        if past:
            events = filter(lambda x: x.end <= datetime.datetime.now(),
                            events)

        if by_me is not None:
            events = (event for event in events if event.by_me == by_me)

        return events

    def get_event_by_id(self, event_id: str) -> Event:
        """Get an event by id."""
        response = service().events().get(
            calendarId=self.calendar_id,
            eventId=event_id
        ).execute()
        return Event.from_service_event(self, response)

    def list_current_events(self, date: Optional[datetime.datetime] = None,
                            margin: datetime.timedelta = datetime.timedelta(days=0), **kwargs) -> Iterator[Event]:
        """List events happening currently."""
        date = date if date is not None else datetime.datetime.now()
        lower_bound, upper_bound = date - margin, date + margin
        return filter(lambda x: x.start <= upper_bound and x.end >= lower_bound, self.list_events(**kwargs))

    def __iter__(self) -> Iterator[Event]:
        """Return iterator."""
        return self.list_events()


class AttendanceStatus(StrEnum):
    """Event status enum."""

    needs_action = "needsAction"
    declined = "declined"
    tentative = "tentative"
    accepted = "accepted"


def _get_event_status(data: dict) -> AttendanceStatus:
    """Get event status from data."""
    if "attendees" in data:
        for attendee in data["attendees"]:
            if attendee.get("self", False):
                return AttendanceStatus(attendee.get("responseStatus", "accepted"))
    return AttendanceStatus.accepted  # Default if no attendees or self not found


@dataclass
class Event:
    """Google Calendar Event repr."""

    calendar: Calendar
    event_id: str
    title: str
    start: datetime.datetime
    end: datetime.datetime
    all_day: bool
    color: int | None
    location: str | None
    by_me: bool
    attendance_status: AttendanceStatus
    organizer: str

    @staticmethod
    def from_service_event(calendar: Calendar, data: dict) -> Event:
        """Generate event from the result of an api query."""
        start = strip_timezone(get_dt_from_google(data["start"]))
        end = strip_timezone(get_dt_from_google(data["end"]))
        by_me = data.get("organizer", {}).get("self", False)
        attendance_status = _get_event_status(data)
        return Event(calendar, data["id"], data["summary"],
                     start, end, "date" in data["start"].keys(),
                     color=(data["color"] if "color" in data.keys() else None),
                     location=(data["location"] if "location" in data.keys() else None),
                     by_me=by_me, attendance_status=attendance_status,
                     organizer=data["organizer"]["email"]
                     )

    @property
    def duration(self) -> datetime.timedelta:
        """Get the event duration."""
        return self.end - self.start

    def __eq__(self, o) -> bool:
        """Compare events."""
        if isinstance(o, str):
            return o == self.event_id or o == self.title
        elif isinstance(o, Event):
            return o.event_id == self.event_id
        return False

    @property
    def attendees(self) -> list[str]:
        """Return attendee emails for this event."""
        svc = self.calendar.service()
        ev = svc.events().get(
            calendarId=self.calendar.calendar_id,
            eventId=self.event_id
        ).execute()
        return [a.get("email") for a in ev.get("attendees", []) if a.get("email")]

    def invite(self, emails: Iterable[str] | str) -> None:
        """Invite participants to the event."""
        if isinstance(emails, str):
            emails = [emails]
        svc = self.calendar.service()
        current_attendees_state = svc.events().get(
            calendarId=self.calendar.calendar_id,
            eventId=self.event_id
        ).execute().get("attendees", [])
        current_attendees_emails = {attendee["email"] for attendee in current_attendees_state if "email" in attendee}
        emails = [email for email in emails if email not in current_attendees_emails]
        print(current_attendees_state, current_attendees_emails, emails)
        svc.events().patch(
            calendarId=self.calendar.calendar_id,
            eventId=self.event_id,
            body={"attendees": current_attendees_state + [{"email": email} for email in emails]},
            sendUpdates="all"
        ).execute()

    def set_location(self, location: str) -> None:
        """Set or change the event location."""
        svc = self.calendar.service()
        svc.events().patch(
            calendarId=self.calendar.calendar_id,
            eventId=self.event_id,
            body={"location": location},
            sendUpdates="all"
        ).execute()
        self.location = location

    def respond_to_invite(self, accept: bool, response_email: str = "mc.xenix@gmail.com") -> None:
        """Respond to invite. Either accept (True) or decline (False)."""
        svc = self.calendar.service()
        response_status = AttendanceStatus.accepted if accept else AttendanceStatus.declined
        svc.events().patch(
            calendarId=self.calendar.calendar_id,
            eventId=self.event_id,
            # TODO: do not hardcode email
            body={"attendees": [{"email": response_email, "responseStatus": response_status}]},
            sendUpdates="all"
        ).execute()
        self.attendance_status = AttendanceStatus(response_status)

    def set_time(self, start: datetime.datetime | datetime.date, end: datetime.datetime | datetime.date,
                 all_day: bool | None = None) -> None:
        """Reschedule the time of the event."""
        if all_day is None:
            all_day = not isinstance(start, datetime.datetime)
        if all_day:
            event = {
                "start": {"date": datetime.datetime.strftime(todt(start), "%Y-%m-%d")},
                "end": {"date": datetime.datetime.strftime(todt(end), "%Y-%m-%d")}
            }
        else:
            event = {
                "start": {"dateTime": get_google_from_dt(start), "timeZone": get_timezone()},
                "end": {"dateTime": get_google_from_dt(end), "timeZone": get_timezone()}
            }
        svc = self.calendar.service()
        svc.events().patch(
            calendarId=self.calendar.calendar_id,
            eventId=self.event_id,
            body=event,
            sendUpdates="all"
        ).execute()

        self.start, self.end = todt(start), todt(end)


if __name__ == '__main__':
    Calendar().create_event('test', datetime.date.today())
    Calendar().create_event('test2', datetime.datetime.now())
