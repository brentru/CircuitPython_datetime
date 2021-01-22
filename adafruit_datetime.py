# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_datetime`
================================================================================
Concrete date/time and related types.

See http://www.iana.org/time-zones/repository/tz-link.html for
time zone and DST data sources.

* Author(s): Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases


"""
import time as _time
import math as _math
from micropython import const

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_DateTime.git"

# Utility functions

# The datetime module exports the following constants:
MINYEAR = const(1)
MAXYEAR = const(9999)
_MAXORDINAL = const(3652059)
_DI400Y = const(146097)
_DI100Y = const(36524)
_DI4Y = const(1461)
# https://svn.python.org/projects/sandbox/trunk/datetime/datetime.py
_DAYS_IN_MONTH = (None, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_DAYS_BEFORE_MONTH = (None, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)

# universally shared
def _cmp(obj_x, obj_y):
    return 0 if obj_x == obj_y else 1 if obj_x > obj_y else -1


def _cmperror(obj_x, obj_y):
    raise TypeError(
        "can't compare '%s' to '%s'" % (type(obj_x).__name__, type(obj_y).__name__)
    )


# time
def _check_time_fields(hour, minute, second, microsecond, fold):
    if not isinstance(hour, int):
        raise TypeError("Hour expected as int")
    if not 0 <= hour <= 23:
        raise ValueError("hour must be in 0..23", hour)
    if not 0 <= minute <= 59:
        raise ValueError("minute must be in 0..59", minute)
    if not 0 <= second <= 59:
        raise ValueError("second must be in 0..59", second)
    if not 0 <= microsecond <= 999999:
        raise ValueError("microsecond must be in 0..999999", microsecond)
    if fold not in (0, 1):  # from CPython API
        raise ValueError("fold must be either 0 or 1", fold)


# name is the offset-producing method, "utcoffset" or "dst".
# offset is what it returned.
# If offset isn't None or timedelta, raises TypeError.
# If offset is None, returns None.
# Else offset is checked for being in range, and a whole # of minutes.
# If it is, its integer value is returned.  Else ValueError is raised.
def _check_utc_offset(name, offset):
    assert name in ("utcoffset", "dst")
    if offset is None:
        return
    if not isinstance(offset, timedelta):
        raise TypeError(
            "tzinfo.%s() must return None "
            "or timedelta, not '%s'" % (name, type(offset))
        )
    if offset % timedelta(minutes=1) or offset.microseconds:
        raise ValueError(
            "tzinfo.%s() must return a whole number "
            "of minutes, got %s" % (name, offset)
        )
    if not -timedelta(1) < offset < timedelta(1):
        raise ValueError(
            "%s()=%s, must be must be strictly between"
            " -timedelta(hours=24) and timedelta(hours=24)" % (name, offset)
        )


# Correctly substitute for %z and %Z escapes in strftime formats.
def _wrap_strftime(time_obj, strftime_fmt, timetuple):
    # Don't call utcoffset() or tzname() unless actually needed.
    f_replace = None  # the string to use for %f
    z_replace = None  # the string to use for %z
    Z_replace = None  # the string to use for %Z

    # Scan strftime_fmt for %z and %Z escapes, replacing as needed.
    newformat = []
    push = newformat.append
    i, n = 0, len(strftime_fmt)
    while i < n:
        ch = strftime_fmt[i]
        i += 1
        if ch == "%":
            if i < n:
                ch = strftime_fmt[i]
                i += 1
                if ch == "f":
                    if f_replace is None:
                        f_replace = "%06d" % getattr(time_obj, "microsecond", 0)
                    newformat.append(f_replace)
                elif ch == "z":
                    if z_replace is None:
                        z_replace = ""
                        if hasattr(time_obj, "utcoffset"):
                            offset = time_obj.utcoffset()
                            if offset is not None:
                                sign = "+"
                                if offset.days < 0:
                                    offset = -offset
                                    sign = "-"
                                h, rest = divmod(offset, timedelta(hours=1))
                                m, rest = divmod(rest, timedelta(minutes=1))
                                s = rest.seconds
                                u = offset.microseconds
                                if u:
                                    z_replace = "%c%02d%02d%02d.%06d" % (
                                        sign,
                                        h,
                                        m,
                                        s,
                                        u,
                                    )
                                elif s:
                                    z_replace = "%c%02d%02d%02d" % (sign, h, m, s)
                                else:
                                    z_replace = "%c%02d%02d" % (sign, h, m)
                    assert "%" not in z_replace
                    newformat.append(z_replace)
                elif ch == "Z":
                    if Z_replace is None:
                        Z_replace = ""
                        if hasattr(time_obj, "tzname"):
                            s = time_obj.tzname()
                            if s is not None:
                                # strftime is going to have at this: escape %
                                Z_replace = s.replace("%", "%%")
                    newformat.append(Z_replace)
                else:
                    push("%")
                    push(ch)
            else:
                push("%")
        else:
            push(ch)
    newformat = "".join(newformat)
    return _time.strftime(newformat, timetuple)


# timezone
def _check_tzname(name):
    """"Just raise TypeError if the arg isn't None or a string."""
    if name is not None and not isinstance(name, str):
        raise TypeError(
            "tzinfo.tzname() must return None or string, " "not '%s'" % type(name)
        )


# date
def _parse_isoformat_date(dtstr):
    # It is assumed that this function will only be called with a
    # string of length exactly 10, and (though this is not used) ASCII-only
    year = int(dtstr[0:4])
    if dtstr[4] != "-":
        raise ValueError("Invalid date separator: %s" % dtstr[4])

    month = int(dtstr[5:7])

    if dtstr[7] != "-":
        raise ValueError("Invalid date separator")

    day = int(dtstr[8:10])

    return [year, month, day]


def _is_leap(year):
    "year -> 1 if leap year, else 0."
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_in_month(year, month):
    "year, month -> number of days in that month in that year."
    assert 1 <= month <= 12, month
    if month == 2 and _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]


def _check_date_fields(year, month, day):
    if not isinstance(year, int):
        raise TypeError("int expected")
    if not MINYEAR <= year <= MAXYEAR:
        raise ValueError("year must be in %d..%d" % (MINYEAR, MAXYEAR), year)
    if not 1 <= month <= 12:
        raise ValueError("month must be in 1..12", month)
    dim = _days_in_month(year, month)
    if not 1 <= day <= dim:
        raise ValueError("day must be in 1..%d" % dim, day)


def _days_before_month(year, month):
    "year, month -> number of days in year preceding first day of month."
    assert 1 <= month <= 12, "month must be in 1..12"
    return _DAYS_BEFORE_MONTH[month] + (month > 2 and _is_leap(year))


def _days_before_year(year):
    "year -> number of days before January 1st of year."
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400


def _ymd2ord(year, month, day):
    "year, month, day -> ordinal, considering 01-Jan-0001 as day 1."
    assert 1 <= month <= 12, "month must be in 1..12"
    dim = _days_in_month(year, month)
    assert 1 <= day <= dim, "day must be in 1..%d" % dim
    return _days_before_year(year) + _days_before_month(year, month) + day


def _build_struct_time(tm_year, tm_month, tm_mday, tm_hour, tm_min, tm_sec, tm_isdst):
    tm_wday = (_ymd2ord(tm_year, tm_month, tm_mday) + 6) % 7
    tm_yday = _days_before_month(tm_year, tm_month) + tm_mday
    return _time.struct_time(
        (
            tm_year,
            tm_month,
            tm_mday,
            tm_hour,
            tm_min,
            tm_sec,
            tm_wday,
            tm_yday,
            tm_isdst,
        )
    )


def _format_time(hh, mm, ss, us, timespec="auto"):
    if timespec != "auto":
        raise NotImplementedError("Only default timespec supported")
    if us:
        spec = "{:02d}:{:02d}:{:02d}.{:06d}"
    else:
        spec = "{:02d}:{:02d}:{:02d}"
    fmt = spec
    return fmt.format(hh, mm, ss, us)


# A 4-year cycle has an extra leap day over what we'd get from pasting
# together 4 single years.
assert _DI4Y == 4 * 365 + 1

# Similarly, a 400-year cycle has an extra leap day over what we'd get from
# pasting together 4 100-year cycles.
assert _DI400Y == 4 * _DI100Y + 1

# OTOH, a 100-year cycle has one fewer leap day than we'd get from
# pasting together 25 4-year cycles.
assert _DI100Y == 25 * _DI4Y - 1


def _ord2ymd(n):
    "ordinal -> (year, month, day), considering 01-Jan-0001 as day 1."

    # n is a 1-based index, starting at 1-Jan-1.  The pattern of leap years
    # repeats exactly every 400 years.  The basic strategy is to find the
    # closest 400-year boundary at or before n, then work with the offset
    # from that boundary to n.  Life is much clearer if we subtract 1 from
    # n first -- then the values of n at 400-year boundaries are exactly
    # those divisible by _DI400Y:
    #
    #     D  M   Y            n              n-1
    #     -- --- ----        ----------     ----------------
    #     31 Dec -400        -_DI400Y       -_DI400Y -1
    #      1 Jan -399         -_DI400Y +1   -_DI400Y      400-year boundary
    #     ...
    #     30 Dec  000        -1             -2
    #     31 Dec  000         0             -1
    #      1 Jan  001         1              0            400-year boundary
    #      2 Jan  001         2              1
    #      3 Jan  001         3              2
    #     ...
    #     31 Dec  400         _DI400Y        _DI400Y -1
    #      1 Jan  401         _DI400Y +1     _DI400Y      400-year boundary
    n -= 1
    n400, n = divmod(n, _DI400Y)
    year = n400 * 400 + 1  # ..., -399, 1, 401, ...

    # Now n is the (non-negative) offset, in days, from January 1 of year, to
    # the desired date.  Now compute how many 100-year cycles precede n.
    # Note that it's possible for n100 to equal 4!  In that case 4 full
    # 100-year cycles precede the desired day, which implies the desired
    # day is December 31 at the end of a 400-year cycle.
    n100, n = divmod(n, _DI100Y)

    # Now compute how many 4-year cycles precede it.
    n4, n = divmod(n, _DI4Y)

    # And now how many single years.  Again n1 can be 4, and again meaning
    # that the desired day is December 31 at the end of the 4-year cycle.
    n1, n = divmod(n, 365)

    year += n100 * 100 + n4 * 4 + n1
    if n1 == 4 or n100 == 4:
        assert n == 0
        return year - 1, 12, 31

    # Now the year is correct, and n is the offset from January 1.  We find
    # the month via an estimate that's either exact or one too large.
    leapyear = n1 == 3 and (n4 != 24 or n100 == 3)
    assert leapyear == _is_leap(year)
    month = (n + 50) >> 5
    preceding = _DAYS_BEFORE_MONTH[month] + (month > 2 and leapyear)
    if preceding > n:  # estimate is too large
        month -= 1
        preceding -= _DAYS_IN_MONTH[month] + (month == 2 and leapyear)
    n -= preceding
    assert 0 <= n < _days_in_month(year, month)

    # Now the year and month are correct, and n is the offset from the
    # start of that month:  we're done!
    return year, month, n + 1


class timedelta:
    """A timedelta object represents a duration, the difference between two dates or times.

    Only days, seconds and microseconds are stored internally. Arguments are converted to those units:
        * A millisecond is converted to 1000 microseconds.
        * A minute is converted to 60 seconds.
        * An hour is converted to 3600 seconds.
        * A week is converted to 7 days.
    and days, seconds and microseconds are then normalized so that the representation is unique, with
        * 0 <= microseconds < 1000000
        * 0 <= seconds < 3600*24 (the number of seconds in one day)
        * -999999999 <= days <= 999999999

    """

    __slots__ = "_days", "_seconds", "_microseconds", "_hashcode"

    def __new__(
        cls,
        days=0,
        seconds=0,
        microseconds=0,
        milliseconds=0,
        minutes=0,
        hours=0,
        weeks=0,
    ):

        # Doing this efficiently and accurately in C is going to be difficult
        # and error-prone, due to ubiquitous overflow possibilities, and that
        # C double doesn't have enough bits of precision to represent
        # microseconds over 10K years faithfully.  The code here tries to make
        # explicit where go-fast assumptions can be relied on, in order to
        # guide the C implementation; it's way more convoluted than speed-
        # ignoring auto-overflow-to-long idiomatic Python could be.

        # Check that all inputs are ints or floats.
        if not all(
            isinstance(i, (int, float))
            for i in [days, seconds, microseconds, milliseconds, minutes, hours, weeks]
        ):
            raise TypeError("Kwargs to this function must be int or float.")

        # Final values, all integer.
        # s and us fit in 32-bit signed ints; d isn't bounded.
        d = s = us = 0

        # Normalize everything to days, seconds, microseconds.
        days += weeks * 7
        seconds += minutes * 60 + hours * 3600
        microseconds += milliseconds * 1000

        # Get rid of all fractions, and normalize s and us.
        # Take a deep breath <wink>.
        if isinstance(days, float):
            dayfrac, days = _math.modf(days)
            daysecondsfrac, daysecondswhole = _math.modf(dayfrac * (24.0 * 3600.0))
            assert daysecondswhole == int(daysecondswhole)  # can't overflow
            s = int(daysecondswhole)
            assert days == int(days)
            d = int(days)
        else:
            daysecondsfrac = 0.0
            d = days
        assert isinstance(daysecondsfrac, float)
        assert abs(daysecondsfrac) <= 1.0
        assert isinstance(d, int)
        assert abs(s) <= 24 * 3600
        # days isn't referenced again before redefinition

        if isinstance(seconds, float):
            secondsfrac, seconds = _math.modf(seconds)
            assert seconds == int(seconds)
            seconds = int(seconds)
            secondsfrac += daysecondsfrac
            assert abs(secondsfrac) <= 2.0
        else:
            secondsfrac = daysecondsfrac
        # daysecondsfrac isn't referenced again
        assert isinstance(secondsfrac, float)
        assert abs(secondsfrac) <= 2.0

        assert isinstance(seconds, int)
        days, seconds = divmod(seconds, 24 * 3600)
        d += days
        s += int(seconds)  # can't overflow
        assert isinstance(s, int)
        assert abs(s) <= 2 * 24 * 3600
        # seconds isn't referenced again before redefinition

        usdouble = secondsfrac * 1e6
        assert abs(usdouble) < 2.1e6  # exact value not critical
        # secondsfrac isn't referenced again

        if isinstance(microseconds, float):
            microseconds = round(microseconds + usdouble)
            seconds, microseconds = divmod(microseconds, 1000000)
            days, seconds = divmod(seconds, 24 * 3600)
            d += days
            s += seconds
        else:
            microseconds = int(microseconds)
            seconds, microseconds = divmod(microseconds, 1000000)
            days, seconds = divmod(seconds, 24 * 3600)
            d += days
            s += seconds
            microseconds = round(microseconds + usdouble)
        assert isinstance(s, int)
        assert isinstance(microseconds, int)
        assert abs(s) <= 3 * 24 * 3600
        assert abs(microseconds) < 3.1e6

        # Just a little bit of carrying possible for microseconds and seconds.
        seconds, us = divmod(microseconds, 1000000)
        s += seconds
        days, s = divmod(s, 24 * 3600)
        d += days

        assert isinstance(d, int)
        assert isinstance(s, int) and 0 <= s < 24 * 3600
        assert isinstance(us, int) and 0 <= us < 1000000

        if abs(d) > 999999999:
            raise OverflowError("timedelta # of days is too large: %d" % d)

        self = object.__new__(cls)
        self._days = d
        self._seconds = s
        self._microseconds = us
        self._hashcode = -1
        return self

    def total_seconds(self):
        """Total seconds in the duration."""
        return (
            (self.days * 86400 + self.seconds) * 10 ** 6 + self.microseconds
        ) / 10 ** 6

    def __repr__(self):
        args = []
        if self._days:
            args.append("days=%d" % self._days)
        if self._seconds:
            args.append("seconds=%d" % self._seconds)
        if self._microseconds:
            args.append("microseconds=%d" % self._microseconds)
        if not args:
            args.append("0")
        return "%s.%s(%s)" % (
            self.__class__.__module__,
            self.__class__.__qualname__,
            ", ".join(args),
        )

    def __str__(self):
        mm, ss = divmod(self._seconds, 60)
        hh, mm = divmod(mm, 60)
        s = "%d:%02d:%02d" % (hh, mm, ss)
        if self._days:

            def plural(n):
                return n, abs(n) != 1 and "s" or ""

            s = ("%d day%s, " % plural(self._days)) + s
        if self._microseconds:
            s = s + ".%06d" % self._microseconds
        return s

    def __neg__(self):
        # for CPython compatibility, we cannot use
        # our __class__ here, but need a real timedelta
        return timedelta(-self._days, -self._seconds, -self._microseconds)


class tzinfo:
    """This is an abstract base class, meaning that this class should not
    be instantiated directly. Define a subclass of tzinfo to capture information
    about a particular time zone.
    An instance of (a concrete subclass of) tzinfo can be passed to the constructors for datetime and time objects. The latter objects view their attributes as being in local time, and the tzinfo object supports methods revealing offset of local time from UTC, the name of the time zone, and DST offset, all relative to a date or time object passed to them.

    """

    __slots__ = ()

    def utcoffset(self, dt):
        """Return offset of local time from UTC, as a timedelta object that is positive east of UTC. """
        raise NotImplementedError("tzinfo subclass must override utcoffset()")

    def tzname(self, dt):
        """Return the time zone name corresponding to the datetime object dt, as a string."""
        raise NotImplemented("tzinfo subclass must override tzname()")


class date:
    """A date object represents a date (year, month and day) in an idealized calendar,
    the current Gregorian calendar indefinitely extended in both directions.
    Objects of this type are always naive.

    """

    __slots__ = "_year", "_month", "_day", "_hashcode"

    def __new__(cls, year, month, day):
        """Creates a new date object.

        :param int year: Year within range, MINYEAR <= year <= MAXYEAR
        :param int month: Month within range, 1 <= month <= 12
        :param int day: Day within range, 1 <= day <= number of days in the given month and year
        """
        _check_date_fields(year, month, day)
        self = object.__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        self._hashcode = -1
        return self

    # Instance attributes, read-only
    @property
    def year(self):
        """Between MINYEAR and MAXYEAR inclusive."""
        return self._year

    @property
    def month(self):
        """Between 1 and 12 inclusive."""
        return self._month

    @property
    def day(self):
        """Between 1 and the number of days in the given month of the given year."""
        return self._day

    # Class methods
    @classmethod
    def fromtimestamp(cls, t):
        """Return the local date corresponding to the POSIX timestamp,
        such as is returned by time.time().
        """
        (
            tm_year,
            tm_mon,
            tm_mday,
            tm_hour,
            tm_min,
            tm_sec,
            tm_wday,
            tm_yday,
            tm_isdst,
        ) = _time.localtime(t)
        return cls(tm_year, tm_mon, tm_mday)

    @classmethod
    def fromordinal(cls, ordinal):
        """Return the date corresponding to the proleptic Gregorian ordinal,
        where January 1 of year 1 has ordinal 1.

        """
        if not ordinal >= 1:
            raise ValueError("ordinal must be >=1")
        y, m, d = _ord2ymd(ordinal)
        return cls(y, m, d)

    @classmethod
    def today(cls):
        """Return the current local date."""
        return cls.fromtimestamp(_time.time())

    @classmethod
    def fromisoformat(cls, date_string):
        """Return a date corresponding to a date_string given in the format YYYY-MM-DD."""
        # TODO - this is not within the datetime impl but we should implement it!
        raise NotImplementedError()

    # Instance methods
    def __repr__(self):
        """Convert to formal string, for repr()."""
        return "%s(%d, %d, %d)" % (
            "datetime." + self.__class__.__name__,
            self._year,
            self._month,
            self._day,
        )

    def replace(self, year=None, month=None, day=None):
        """Return a date with the same value, except for those parameters
        given new values by whichever keyword arguments are specified.
        If no keyword arguments are specified - values are obtained from
        datetime object.

        """
        raise NotImplementedError()

    def timetuple(self):
        """Return a time.struct_time such as returned by time.localtime().
        The hours, minutes and seconds are 0, and the DST flag is -1.

        """
        return _build_struct_time(self._year, self._month, self._day, 0, 0, 0, -1)

    def toordinal(self):
        """Return the proleptic Gregorian ordinal of the date, where January 1 of
        year 1 has ordinal 1.
        """
        return _ymd2ord(self._year, self._month, self._day)

    def weekday(self):
        """Return the day of the week as an integer, where Monday is 0 and Sunday is 6."""
        return (self.toordinal() + 6) % 7

    # ISO date
    def isoweekday(self):
        """Return the day of the week as an integer, where Monday is 1 and Sunday is 7."""
        return self.toordinal() % 7 or 7

    def isoformat(self):
        """Return a string representing the date in ISO 8601 format, YYYY-MM-DD:"""
        return "%04d-%02d-%02d" % (self._year, self._month, self._day)

    # For a date d, str(d) is equivalent to d.isoformat()
    __str__ = isoformat

    # Comparisons of date objects with other

    def __eq__(self, other):
        if isinstance(other, date):
            return self._cmp(other) == 0
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, date):
            return self._cmp(other) <= 0
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, date):
            return self._cmp(other) < 0
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, date):
            return self._cmp(other) >= 0
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, date):
            return self._cmp(other) > 0
        return NotImplemented

    def _cmp(self, other):
        assert isinstance(other, date)
        y, m, d = self._year, self._month, self._day
        y2, m2, d2 = other._year, other._month, other._day
        return _cmp((y, m, d), (y2, m2, d2))

    def __hash__(self):
        "Hash."
        if self._hashcode == -1:
            self._hashcode = hash(self._getstate())
        return self._hashcode

    # Pickle support
    def _getstate(self):
        yhi, ylo = divmod(self._year, 256)
        return (bytes([yhi, ylo, self._month, self._day]),)

    def _setstate(self, string):
        yhi, ylo, self._month, self._day = string
        self._year = yhi * 256 + ylo

    def __reduce__(self):
        return (self.__class__, self._getstate())


_date_class = date


class time:
    """A time object represents a (local) time of day, independent of
    any particular day, and subject to adjustment via a tzinfo object.

    """

    # Using __slots__ to reduce object's RAM usage
    __slots__ = (
        "_hour",
        "_minute",
        "_second",
        "_microsecond",
        "_tzinfo",
        "_hashcode",
        "_fold",
    )

    def __new__(cls, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0):
        _check_time_fields(hour, minute, second, microsecond, fold)
        # TODO: Impl. tzinfo checks
        # _check_tzinfo_arg(tzinfo)
        self = object.__new__(cls)
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        self._tzinfo = tzinfo
        self._fold = fold
        self._hashcode = -1
        return self

    # Instance attributes (read-only)
    @property
    def hour(self):
        """In range(24)."""
        return self._hour

    @property
    def minute(self):
        """In range(60)."""
        return self._minute

    @property
    def second(self):
        """In range(60)."""
        return self._second

    @property
    def microsecond(self):
        """In range(1000000)."""
        return self._microsecond

    @property
    def tzinfo(self):
        """The object passed as the tzinfo argument to
        the time constructor, or None if none was passed.
        """
        return self._microsecond

    # Standard conversions and comparisons
    # From CPython, https://github.com/python/cpython/blob/master/Lib/datetime.py
    def __eq__(self, other):
        if not isinstance(other, time):
            return NotImplemented
        return self._cmp(other, allow_mixed=True) == 0

    def __le__(self, other):
        if not isinstance(other, time):
            return NotImplemented
        return self._cmp(other) <= 0

    def __lt__(self, other):
        if not isinstance(other, time):
            return NotImplemented
        return self._cmp(other) < 0

    def __ge__(self, other):
        if not isinstance(other, time):
            return NotImplemented
        return self._cmp(other) >= 0

    def __gt__(self, other):
        if not isinstance(other, time):
            return NotImplemented
        return self._cmp(other) > 0

    def _cmp(self, other, allow_mixed=False):
        assert isinstance(other, time)
        mytz = self._tzinfo
        ottz = other._tzinfo
        myoff = otoff = None

        if mytz is ottz:
            base_compare = True
        else:
            myoff = self.utcoffset()
            otoff = other.utcoffset()
            base_compare = myoff == otoff

        if base_compare:
            return _cmp(
                (self._hour, self._minute, self._second, self._microsecond),
                (other._hour, other._minute, other._second, other._microsecond),
            )
        if myoff is None or otoff is None:
            if allow_mixed:
                return 2  # arbitrary non-zero value
            else:
                raise TypeError("cannot compare naive and aware times")
        myhhmm = self._hour * 60 + self._minute - myoff // timedelta(minutes=1)
        othhmm = other._hour * 60 + other._minute - otoff // timedelta(minutes=1)
        return _cmp(
            (myhhmm, self._second, self._microsecond),
            (othhmm, other._second, other._microsecond),
        )

    # from CPython
    # https://github.com/python/cpython/blob/master/Lib/datetime.py
    def __hash__(self):
        """Hash."""
        if self._hashcode == -1:
            if self._fold:
                t = self.replace(fold=0)
            else:
                t = self
            tzoff = t.utcoffset()
            if not tzoff:  # zero or None
                self._hashcode = hash(t._getstate()[0])
            else:
                h, m = divmod(
                    timedelta(hours=self.hour, minutes=self.minute) - tzoff,
                    timedelta(hours=1),
                )
                assert not m % timedelta(minutes=1), "whole minute"
                m //= timedelta(minutes=1)
                if 0 <= h < 24:
                    self._hashcode = hash(time(h, m, self.second, self.microsecond))
                else:
                    self._hashcode = hash((h, m, self.second, self.microsecond))
        return self._hashcode

    # Instance methods
    def replace():
        raise NotImplementedError

    def isoformat(self, timespec="auto"):
        """Return a string representing the time in ISO 8601 format, one of:
        HH:MM:SS.ffffff, if microsecond is not 0

        HH:MM:SS, if microsecond is 0

        HH:MM:SS.ffffff+HH:MM[:SS[.ffffff]], if utcoffset() does not return None

        HH:MM:SS+HH:MM[:SS[.ffffff]], if microsecond is 0 and utcoffset() does not return None

        """
        s = _format_time(
            self._hour, self._minute, self._second, self._microsecond, timespec
        )
        tz = self._tzstr()
        if tz:
            s += tz
        return s

    # For a time t, str(t) is equivalent to t.isoformat()
    __str__ = isoformat

    def _tzstr(self, sep=":"):
        """Return formatted timezone offset (+xx:xx) or None."""
        off = self.utcoffset()
        if off is not None:
            if off.days < 0:
                sign = "-"
                off = -off
            else:
                sign = "+"
            hh, mm = divmod(off, timedelta(hours=1))
            assert not mm % timedelta(minutes=1), "whole minute"
            mm //= timedelta(minutes=1)
            assert 0 <= hh < 24
            off = "%s%02d%s%02d" % (sign, hh, sep, mm)
        return off

    def strftime(self, fmt):
        """Format using strftime().  The date part of the timestamp passed
        to underlying strftime should not be used.
        """
        # The year must be >= 1000 else Python's strftime implementation
        # can raise a bogus exception.
        timetuple = (1900, 1, 1, self._hour, self._minute, self._second, 0, 1, -1)
        return _wrap_strftime(self, fmt, timetuple)

    # from CPython
    # https://github.com/python/cpython/blob/master/Lib/datetime.py
    def __format__(self, fmt):
        if not isinstance(fmt, str):
            raise TypeError("must be str, not %s" % type(fmt).__name__)
        if len(fmt) != 0:
            return self.strftime(fmt)
        return str(self)

    def __repr__(self):
        """Convert to formal string, for repr()."""
        if self._microsecond != 0:
            s = ", %d, %d" % (self._second, self._microsecond)
        elif self._second != 0:
            s = ", %d" % self._second
        else:
            s = ""
        s = "%s.%s(%d, %d%s)" % (
            self.__class__.__module__,
            self.__class__.__qualname__,
            self._hour,
            self._minute,
            s,
        )
        if self._tzinfo is not None:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self._tzinfo + ")"
        if self._fold:
            assert s[-1:] == ")"
            s = s[:-1] + ", fold=1)"
        return s

    # Timezone functions
    def utcoffset(self):
        """Return the timezone offset in minutes east of UTC (negative west of
        UTC)."""
        if self._tzinfo is None:
            return None
        offset = self._tzinfo.utcoffset(None)
        _check_utc_offset("utcoffset", offset)
        return offset

    def tzname(self):
        """Return the timezone name.

        Note that the name is 100% informational -- there's no requirement that
        it mean anything in particular. For example, "GMT", "UTC", "-500",
        "-5:00", "EDT", "US/Eastern", "America/New York" are all valid replies.
        """
        if self._tzinfo is None:
            return None
        name = self._tzinfo.tzname(None)
        _check_tzname(name)
        return name

    def dst():
        raise NotImplementedError()

    # Pickle support
    def _getstate(self, protocol=3):
        us2, us3 = divmod(self._microsecond, 256)
        us1, us2 = divmod(us2, 256)
        h = self._hour
        if self._fold and protocol > 3:
            h += 128
        basestate = bytes([h, self._minute, self._second, us1, us2, us3])
        if self._tzinfo is None:
            return (basestate,)
        else:
            return (basestate, self._tzinfo)


# todo: move to bottom?
_time_class = time  # so functions w/ args named "time" can get at the class


class datetime(date):
    """A datetime object is a single object containing all the information from a date object and a time object.
    Like a date object, datetime assumes the current Gregorian calendar extended in both directions; like a time object, datetime assumes there are exactly 3600*24 seconds in every day.

    """

    def __new__(
        cls,
        year,
        month,
        day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=None,
        *,
        fold=0
    ):
        # check date and time fields
        _check_date_fields(year, month, day)
        _check_time_fields(hour, minute, second, microsecond, fold)
        # TODO: TZINFO support
        # _check_tzinfo_arg(tzinfo)

        self = object.__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        self._tzinfo = tzinfo
        self._fold = fold
        self._hashcode = -1
        return self

    # Read-only instance attributes
    @property
    def year(self):
        """Between MINYEAR and MAXYEAR inclusive."""
        return self._year

    @property
    def month(self):
        """Between 1 and 12 inclusive."""
        return self._month

    @property
    def day(self):
        """Between 1 and the number of days in the given month of the given year."""
        return self._day

    @property
    def hour(self):
        """In range(24)."""
        return self._hour

    @property
    def minute(self):
        """In range (60)"""
        return self._minute

    @property
    def second(self):
        """In range (60)"""
        return self._second

    @property
    def microsecond(self):
        """In range (1000000)"""
        return self._microsecond

    @property
    def tzinfo(self):
        """The object passed as the tzinfo argument to the datetime constructor,
        or None if none was passed.
        """
        return self._tzinfo

    # Class methods

    @classmethod
    def fromtimestamp(cls, timestamp):
        """Return the local date and time corresponding to the POSIX timestamp,
        such as is returned by time.time(). If optional argument tz is None or not
        specified, the timestamp is converted to the platform’s local date and time,
        and the returned datetime object is naive.

        """
        y, m, d, hh, mm, ss, weekday, jday, dst = _time.localtime(timestamp)
        return cls(y, m, d)

    # NOTE: now() is preferred over today() and utcnow()
    @classmethod
    def now(cls, tz=None):
        """Return the current local date and time."""
        return cls.fromtimestamp(_time.time(), tz)

    @classmethod
    def utcfromtimestamp(cls, timestamp):
        """Return the UTC datetime corresponding to the POSIX timestamp, with tzinfo None"""
        return cls.fromtimestamp(timestamp)

    # from CPython
    # https://github.com/python/cpython/blob/master/Lib/datetime.py
    @classmethod
    def fromisoformat(cls, date_string):
        """Return a datetime corresponding to a date_string in one of the
        formats emitted by date.isoformat() and datetime.isoformat().
        :param str date_string: ISO-formatted date or datetime string.

        """
        # TODO!
        pass

    # Instance methods
    def date(self):
        """Return date object with same year, month and day."""
        return _date_class(self._year, self._month, self._day)

    def time(self):
        """Return time object with same hour, minute, second, microsecond and fold.
        tzinfo is None. See also method timetz().
        """
        return _time_class(
            self._hour, self._minute, self._second, self._microsecond, None, self._fold
        )

    def timetuple(self):
        """Return local time tuple compatible with time.localtime()."""
        # TODO: Requires tzinfo and dst()
        raise NotImplementedError
        dst = self.dst()
        if dst is None:
            dst = -1
        elif dst:
            dst = 1
        else:
            dst = 0
        return _build_struct_time(
            self.year, self.month, self.day, self.hour, self.minute, self.second, dst
        )

    def utcoffset(self):
        if self._tzinfo is None:
            return None
        offset = self._tzinfo.utcoffset(self)
        _check_utc_offset("utcoffset", offset)
        return offset

    def toordinal(self):
        """Return the proleptic Gregorian ordinal of the date."""
        return _ymd2ord(self._year, self._month, self._day)

    def timestamp(self):
        "Return POSIX timestamp as float"
        if not self._tzinfo is None:
            return (self - _EPOCH).total_seconds()
        s = self._mktime()
        return s + self.microsecond / 1e6

    def weekday(self):
        """Return the day of the week as an integer, where Monday is 0 and Sunday is 6."""
        return (self.toordinal() + 6) % 7

    def isoweekday(self):
        """Return the day of the week as an integer, where Monday is 1 and Sunday is 7. """
        return self.toordinal() % 7 or 7

    # Comparisons of datetime objects.
    def __eq__(self, other):
        if not isinstance(other, datetime):
            return False
        return self._cmp(other, allow_mixed=True) == 0

    def __le__(self, other):
        if not isinstance(other, datetime):
            _cmperror(self, other)
        return self._cmp(other) <= 0

    def __lt__(self, other):
        if not isinstance(other, datetime):
            _cmperror(self, other)
        return self._cmp(other) < 0

    def __ge__(self, other):
        if not isinstance(other, datetime):
            _cmperror(self, other)
        return self._cmp(other) >= 0

    def __gt__(self, other):
        if not isinstance(other, datetime):
            _cmperror(self, other)
        return self._cmp(other) > 0

    def _cmp(self, other, allow_mixed=False):
        assert isinstance(other, datetime)
        mytz = self._tzinfo
        ottz = other.tzinfo
        myoff = otoff = None

        if mytz is ottz:
            base_compare = True
        else:
            myoff = self.utcoffset()
            otoff = other.utcoffset()
            # Assume that allow_mixed means that we are called from __eq__
            if allow_mixed:
                if myoff != self.replace(fold=not self._fold).utcoffset():
                    return 2
                if otoff != other.replace(fold=not other.fold).utcoffset():
                    return 2
            base_compare = myoff == otoff

        if base_compare:
            return _cmp(
                (
                    self._year,
                    self._month,
                    self._day,
                    self._hour,
                    self._minute,
                    self._second,
                    self._microsecond,
                ),
                (
                    other.year,
                    other.month,
                    other.day,
                    other.hour,
                    other.minute,
                    other.second,
                    other.microsecond,
                ),
            )
        if myoff is None or otoff is None:
            if not allow_mixed:
                raise TypeError("cannot compare naive and aware datetimes")
            return 2  # arbitrary non-zero value
        # XXX What follows could be done more efficiently...
        diff = self - other  # this will take offsets into account
        if diff.days < 0:
            return -1
        return diff and 1 or 0

    def __add__(self, other):
        "Add a datetime and a timedelta."
        if not isinstance(other, timedelta):
            return NotImplemented
        delta = timedelta(
            self.toordinal(),
            hours=self._hour,
            minutes=self._minute,
            seconds=self._second,
            microseconds=self._microsecond,
        )
        delta += other
        hour, rem = divmod(delta.seconds, 3600)
        minute, second = divmod(rem, 60)
        if 0 < delta.days <= _MAXORDINAL:
            return type(self).combine(
                date.fromordinal(delta.days),
                time(hour, minute, second, delta.microseconds, tzinfo=self._tzinfo),
            )
        raise OverflowError("result out of range")

    __radd__ = __add__

    def __sub__(self, other):
        "Subtract two datetimes, or a datetime and a timedelta."
        if not isinstance(other, datetime):
            if isinstance(other, timedelta):
                return self + -other
            return NotImplemented

        days1 = self.toordinal()
        days2 = other.toordinal()
        secs1 = self._second + self._minute * 60 + self._hour * 3600
        secs2 = other._second + other._minute * 60 + other._hour * 3600
        base = timedelta(
            days1 - days2, secs1 - secs2, self._microsecond - other._microsecond
        )
        if self._tzinfo is other._tzinfo:
            return base
        myoff = self.utcoffset()
        otoff = other.utcoffset()
        if myoff == otoff:
            return base
        if myoff is None or otoff is None:
            raise TypeError("cannot mix naive and timezone-aware time")
        return base + otoff - myoff

    def __hash__(self):
        if self._hashcode == -1:
            t = self
            tzoff = t.utcoffset()
            if tzoff is None:
                self._hashcode = hash(t._getstate()[0])
            else:
                days = _ymd2ord(self.year, self.month, self.day)
                seconds = self.hour * 3600 + self.minute * 60 + self.second
                self._hashcode = hash(
                    timedelta(days, seconds, self.microsecond) - tzoff
                )
        return self._hashcode


# TODO: This isn't right...
# _EPOCH = datetime(1970, 1, 1)
