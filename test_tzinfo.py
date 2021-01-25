from adafruit_datetime import timedelta, datetime, timezone

dt = datetime(1970, 1, 1, tzinfo=timezone.utc)
print(dt)
print(dt.utcoffset())

"""dt = datetime.now(timezone=timezone.utc)
print(dt)"""