import datetime
import re

from dateutil.parser import parse as dt_parse

ATTRIBUTE_LIKE = re.compile('^(?P<attr_name>[^:]+):(?:\w+)?(?P<attr_value>[^:]+)$')


class Event:
    def __init__(self, label, start_datetime, end_datetime, description):
        self.label = label
        self.start_datetime = Event._adapt_datetime_input(start_datetime)
        self.end_datetime = Event._adapt_datetime_input(end_datetime)
        self.description = description
        self.description_attributes = dict()
        if self.description:
            for line in self.description.split('\n'):
                match = ATTRIBUTE_LIKE.match(line)
                if match:
                    self.description_attributes[match.group('attr_name')] = match.group('attr_value')

    @staticmethod
    def from_gcal_response(response):
        events = []
        for item in response["items"]:
            labels = [s.strip() for s in item["summary"].split(", ")]
            start_datetime = item["start"]["dateTime"]
            end_datetime = item["end"]["dateTime"]
            description = item["description"] if "description" in item else None
            for label in labels:
                events.append(Event(label, start_datetime, end_datetime, description))
        return events

    def split_by_date(self):
        dates = list(Event._daterange(self.start_datetime, self.end_datetime))
        ind_date = 0
        start_datetime = self.start_datetime
        events = []
        while ind_date < len(dates):
            end_datetime = self.end_datetime
            if (ind_date + 1) < len(dates) and dates[ind_date + 1] < self.end_datetime:
                end_datetime = dates[ind_date + 1]
            new_event = Event(self.label, start_datetime, end_datetime, self.description)
            events.append(new_event)
            start_datetime = new_event.end_datetime
            ind_date += 1
        return events

    def duration(self):
        return self.end_datetime - self.start_datetime

    def __repr__(self):
        return f"Event('{self.label}', '{self.start_datetime.isoformat()}', '{self.end_datetime.isoformat()}')"

    @staticmethod
    def _adapt_datetime_input(arg):
        if isinstance(arg, datetime.datetime):
            return arg
        elif isinstance(arg, str):
            return dt_parse(arg)
        else:
            raise Exception("Not a valid datetime input!")

    @staticmethod
    def _daterange(date1, date2):
        for n in range(int((date2 - date1).days) + 1):
            yield date1 + datetime.timedelta(n)
