import sys
import unittest
from test_date import TestDate
# CPython standard implementation
from datetime import datetime as cpython_datetime
from datetime import MINYEAR, MAXYEAR
# CircuitPython subset implementation
sys.path.append("..")
from adafruit_datetime import datetime as cpy_datetime

class SubclassDatetime(cpy_datetime):
    sub_var = 1

class TestDateTime(TestDate):
    theclass = cpy_datetime
    theclass_cpython = cpython_datetime

    def test_basic_attributes(self):
        dt = self.theclass(2002, 3, 1, 12, 0)
        dt2 = self.theclass_cpython(2002, 3, 1, 12, 0)
        # test circuitpython basic attributes
        self.assertEqual(dt.year, 2002)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)
        self.assertEqual(dt.microsecond, 0)
        # test circuitpython basic attributes against cpython basic attributes
        self.assertEqual(dt.year, dt2.year)
        self.assertEqual(dt.month, dt2.month)
        self.assertEqual(dt.day, dt2.day)
        self.assertEqual(dt.hour, dt2.hour)
        self.assertEqual(dt.minute, dt2.minute)
        self.assertEqual(dt.second, dt2.second)
        self.assertEqual(dt.microsecond, dt2.microsecond)


    def test_ordinal_conversions(self):
        # Check some fixed values.
        for y, m, d, n in [(1, 1, 1, 1),      # calendar origin
                           (1, 12, 31, 365),
                           (2, 1, 1, 366),
                           # first example from "Calendrical Calculations"
                           (1945, 11, 12, 710347)]:
            d = self.theclass(y, m, d)
            self.assertEqual(n, d.toordinal())
            fromord = self.theclass.fromordinal(n)
            self.assertEqual(d, fromord)
            if hasattr(fromord, "hour"):
            # if we're checking something fancier than a date, verify
            # the extra fields have been zeroed out
                self.assertEqual(fromord.hour, 0)
                self.assertEqual(fromord.minute, 0)
                self.assertEqual(fromord.second, 0)
                self.assertEqual(fromord.microsecond, 0)

        # Check first and last days of year spottily across the whole
        # range of years supported.
        for year in range(MINYEAR, MAXYEAR+1, 7):
            # Verify (year, 1, 1) -> ordinal -> y, m, d is identity.
            d = self.theclass(year, 1, 1)
            n = d.toordinal()
            d2 = self.theclass.fromordinal(n)
            self.assertEqual(d, d2)
            # Verify that moving back a day gets to the end of year-1.
            if year > 1:
                d = self.theclass.fromordinal(n-1)
                d2 = self.theclass(year-1, 12, 31)
                self.assertEqual(d, d2)
                self.assertEqual(d2.toordinal(), n-1)

        # Test every day in a leap-year and a non-leap year.
        dim = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        for year, isleap in (2000, True), (2002, False):
            n = self.theclass(year, 1, 1).toordinal()
            for month, maxday in zip(range(1, 13), dim):
                if month == 2 and isleap:
                    maxday += 1
                for day in range(1, maxday+1):
                    d = self.theclass(year, month, day)
                    self.assertEqual(d.toordinal(), n)
                    self.assertEqual(d, self.theclass.fromordinal(n))
                    n += 1

    # TODO: Failing on Min!
    def test_extreme_ordinals(self):
        a = self.theclass.min
        a = self.theclass(a.year, a.month, a.day)  # get rid of time parts
        aord = a.toordinal()
        b = a.fromordinal(aord)
        self.assertEqual(a, b)

        self.assertRaises(ValueError, lambda: a.fromordinal(aord - 1))

        b = a + timedelta(days=1)
        self.assertEqual(b.toordinal(), aord + 1)
        self.assertEqual(b, self.theclass.fromordinal(aord + 1))

        a = self.theclass.max
        a = self.theclass(a.year, a.month, a.day)  # get rid of time parts
        aord = a.toordinal()
        b = a.fromordinal(aord)
        self.assertEqual(a, b)

        self.assertRaises(ValueError, lambda: a.fromordinal(aord + 1))

        b = a - timedelta(days=1)
        self.assertEqual(b.toordinal(), aord - 1)
        self.assertEqual(b, self.theclass.fromordinal(aord - 1))