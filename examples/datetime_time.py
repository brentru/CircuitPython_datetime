# Example of working with a `time` object
from adafruit_datetime import time, timezone

# Create a new time object
t = time(12, 10, 30, tzinfo=timezone.utc)

# ISO 8601 formatted string
iso_time = t.isoformat()
print('ISO8601-Formatted Time:', iso_time)

# Timezone name
print("Timezone Name:", t.tzname())

# Return a string representing the time, controlled by an explicit format string
strf_time = t.strftime("%H:%M:%S %Z")
print('Formatted time string:', strf_time)

# Specifies a format string in formatted string literals
print('The time is {:%H:%M}.'.format(t))