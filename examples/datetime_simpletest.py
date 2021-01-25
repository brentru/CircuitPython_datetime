from adafruit_datetime import datetime, date, time, timezone

# Using datetime.combine()
d = date(2005, 7, 14)
print(d)
t = time(12, 30)
print(datetime.combine(d, t))

# Using datetime.now()
print('Current time (GMT +1):', datetime.now())
print('Current UTC time: ', datetime.now(timezone.utc))

# Using datetime.timetuple() to get tuple of all attributes
dt = datetime(2006, 11, 21, 16, 30)
tt = dt.timetuple()
for it in tt:
    print(it)

# Formatting a datetime
print('The {1} is {0:%d}, the {2} is {0:%B}, the {3} is {0:%I:%M%p}.'.format(dt, "day", "month", "time"))