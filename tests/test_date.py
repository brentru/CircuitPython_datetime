import sys
import unittest
# CPython standard implementation
from datetime import date as cpython_date
from datetime import MINYEAR, MAXYEAR
# CircuitPython subset implementation
sys.path.append("..")
from adafruit_datetime import date as cpy_date

class TestDate(unittest.TestCase):

    def test_basic_attributes(self):
        dt = cpy_date(2002, 3, 1)
        dt_2 = cpython_date(2002, 3, 1)
        self.assertEqual(dt.year, dt_2.year)
        self.assertEqual(dt.month, dt_2.month)
        self.assertEqual(dt.day, dt_2.day)

    def test_bad_constructor_arguments(self):
        # bad years
        cpy_date(MINYEAR, 1, 1)  # no exception
        cpy_date(MAXYEAR, 1, 1)  # no exception
        self.assertRaises(ValueError, cpy_date, MINYEAR-1, 1, 1)
        self.assertRaises(ValueError, cpy_date, MAXYEAR+1, 1, 1)
        # bad months
        cpy_date(2000, 1, 1)    # no exception
        cpy_date(2000, 12, 1)   # no exception
        self.assertRaises(ValueError, cpy_date, 2000, 0, 1)
        self.assertRaises(ValueError, cpy_date, 2000, 13, 1)
        # bad days
        cpy_date(2000, 2, 29)   # no exception
        cpy_date(2004, 2, 29)   # no exception
        cpy_date(2400, 2, 29)   # no exception
        self.assertRaises(ValueError, cpy_date, 2000, 2, 30)
        self.assertRaises(ValueError, cpy_date, 2001, 2, 29)
        self.assertRaises(ValueError, cpy_date, 2100, 2, 29)
        self.assertRaises(ValueError, cpy_date, 1900, 2, 29)
        self.assertRaises(ValueError, cpy_date, 2000, 1, 0)
        self.assertRaises(ValueError, cpy_date, 2000, 1, 32)

    def test_hash_equality(self):
        d = cpy_date(2000, 12, 31)
        e = cpy_date(2000, 12, 31)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

        d = cpy_date(2001,  1,  1)
        e = cpy_date(2001,  1,  1)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

    def test_fromtimestamp(self):
        import time

        # Try an arbitrary fixed value.
        year, month, day = 1999, 9, 19
        ts = time.mktime((year, month, day, 0, 0, 0, 0, 0, -1))
        d = cpy_date.fromtimestamp(ts)
        self.assertEqual(d.year, year)
        self.assertEqual(d.month, month)
        self.assertEqual(d.day, day)

    def test_weekday(self):
        for i in range(7):
            # March 4, 2002 is a Monday
            self.assertEqual(cpy_date(2002, 3, 4+i).weekday(), cpython_date(2002, 3, 4+i).weekday())
            self.assertEqual(cpy_date(2002, 3, 4+i).isoweekday(), cpython_date(2002, 3, 4+i).isoweekday())
            # January 2, 1956 is a Monday
            self.assertEqual(cpy_date(1956, 1, 2+i).weekday(), cpython_date(1956, 1, 2+i).weekday())
            self.assertEqual(cpy_date(1956, 1, 2+i).isoweekday(), cpython_date(1956, 1, 2+i).isoweekday())


if __name__ == '__main__':
    unittest.main()