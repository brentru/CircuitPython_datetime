import sys
import unittest
# CPython standard implementation
from datetime import date as cpython_date
from datetime import MINYEAR, MAXYEAR
# CircuitPython subset implementation
sys.path.append("..")
from adafruit_datetime import date as cpy_date

class TestDates(unittest.TestCase):

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
        # same thing
        e = cpy_date(2000, 12, 31)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

        d = cpy_date(2001,  1,  1)
        # same thing
        e = cpy_date(2001,  1,  1)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

    # TODO: Ordinal conversion failure

if __name__ == '__main__':
    unittest.main()