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

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_DateTime.git"

# The datetime module exports the following constants:
MINYEAR = 1
MAXYEAR = 9999

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
    
    # Class attributes
    @classmethod
    def min(cls):
        """The earliest representable date, date(MINYEAR, 1, 1)."""
        return cls(1, 1, 1)

    @classmethod
    def max(cls):
        """The latest representable date, date(MAXYEAR, 12, 31)."""
        return cls(9999, 12, 31)

    @classmethod
    def resolution():
        """The smallest possible difference between non-equal date objects, timedelta(days=1)."""
        raise NotImplementedError()