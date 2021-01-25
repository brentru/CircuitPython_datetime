from adafruit_datetime import time, tzinfo, timedelta, timezone

# Create a new time object
t = time(12, 10, 30, tzinfo=timezone.utc)
print(t)

# ISO 8601 formatted string
print(t.isoformat())

# Timezone name
print(t.tzname())

# Return a string representing the time, controlled by an explicit format string
print(t.strftime("%H:%M:%S %Z"))

# Specifies a format string in formatted string literals
print('The {} is {:%H:%M}.'.format("time", t))
