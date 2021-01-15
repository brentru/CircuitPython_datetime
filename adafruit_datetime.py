# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_datetime`
================================================================================

Basic date and time types


* Author(s): Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases


"""
import time
import math

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_DateTime.git"

# Utility functions

# The datetime module exports the following constants:
MINYEAR = 1
MAXYEAR = 9999

# https://svn.python.org/projects/sandbox/trunk/datetime/datetime.py
_DAYS_IN_MONTH = [None, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_DAYS_BEFORE_MONTH = [None, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

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
        raise TypeError('int expected')
    if not MINYEAR <= year <= MAXYEAR:
        raise ValueError('year must be in %d..%d' % (MINYEAR, MAXYEAR), year)
    if not 1 <= month <= 12:
        raise ValueError('month must be in 1..12', month)
    dim = _days_in_month(year, month)
    if not 1 <= day <= dim:
        raise ValueError('day must be in 1..%d' % dim, day)

def _days_before_month(year, month):
    "year, month -> number of days in year preceding first day of month."
    assert 1 <= month <= 12, 'month must be in 1..12'
    return _DAYS_BEFORE_MONTH[month] + (month > 2 and _is_leap(year))

def _ymd2ord(year, month, day):
    "year, month, day -> ordinal, considering 01-Jan-0001 as day 1."
    assert 1 <= month <= 12, 'month must be in 1..12'
    dim = _days_in_month(year, month)
    assert 1 <= day <= dim, ('day must be in 1..%d' % dim)
    return (_days_before_year(year) +
            _days_before_month(year, month) +
            day)


def _build_struct_time(tm_year, tm_month, tm_mday, tm_hour, tm_min, tm_sec, tm_isdst):
    tm_wday = (_ymd2ord(tm_year, tm_month, tm_mday) + 6) % 7
    tm_yday = _days_before_month(tm_year, tm_month) + tm_mday
    return time.struct_time((tm_year, tm_month, tm_mday,
                             tm_hour, tm_min, tm_sec, tm_wday,
                             tm_yday, tm_isdst))

def _days_before_year(year):
    "year -> number of days before January 1st of year."
    y = year - 1
    return y*365 + y//4 - y//100 + y//400

_DI400Y = _days_before_year(401)    # number of days in 400 years
_DI100Y = _days_before_year(101)    #    "    "   "   " 100   "
_DI4Y   = _days_before_year(5)      #    "    "   "   "   4   "

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
    year = n400 * 400 + 1   # ..., -399, 1, 401, ...

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
        return year-1, 12, 31

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
    return year, month, n+1

class date:
    """A date object represents a date (year, month and day) in an idealized calendar,
    the current Gregorian calendar indefinitely extended in both directions.
    Objects of this type are always naive.

    """
    def __new__(cls, year, month, day):
        """Creates a new date object.

        :param int year: Year within range, MINYEAR <= year <= MAXYEAR
        :param int month: Month within range, 1 <= month <= 12
        :param int day: Day within range, 1 <= day <= number of days in the given month and year
        """
        _check_date_fields(year, month, day)
        instance = object.__new__(cls)
        instance._year = year
        instance._month = month
        instance._day = day
        return instance

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
        tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst = time.localtime(t)
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
        return cls.fromtimestamp(time.time())

    @classmethod
    def fromisoformat(cls, date_string):
        """Return a date corresponding to a date_string given in the format YYYY-MM-DD."""
        # TODO - this is not within the datetime impl but we should implement it!
        raise NotImplementedError()

    # TODO: Add class attributes like min, max

    # Instance methods
    def __repr__(self):
        """Convert to formal string, for repr()."""
        return "%s(%d, %d, %d)" % ('datetime.' + self.__class__.__name__,
                                   self._year,
                                   self._month,
                                   self._day)

    def replace(self, year=None, month=None, day=None):
        """Return a date with the same value, except for those parameters
        given new values by whichever keyword arguments are specified.
        If no keyword arguments are specified - values are obtained from
        datetime object.

        """
        # Use CPython expected arguments:
        # date.replace(year=self.year, month=self.month, day=self.day)
        if year is None:
            year = year
        if month is None:
            month = month
        if day is None:
            day = day
        _check_date_fields(year, month, day)
        return date(year, month, day)
    
    def timetuple(self):
        """Return a time.struct_time such as returned by time.localtime().
        The hours, minutes and seconds are 0, and the DST flag is -1.

        """
        return _build_struct_time(self._year, self._month, self._day,
                                  0, 0, 0, -1)