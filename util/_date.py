import datetime
import pytz


UTC = pytz.timezone("UTC")
SERVER_TIMEZONE = pytz.timezone("Europe/Berlin")


def to_utc(dt):
    # dt = dt.replace(tz_info=SERVER_TIMEZONE)
    return dt.astimezone(UTC)#.replace(tzinfo=None)


def from_utc(dt):
    return dt.replace(tzinfo=UTC).astimezone(SERVER_TIMEZONE).replace(tzinfo=None)
