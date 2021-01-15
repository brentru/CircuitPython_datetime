import sys
import unittest
# CPython standard implementation
from datetime import date as cpython_date
# CircuitPython subset implementation
sys.path.append("..")
from adafruit_datetime import date

class TestDates(unittest.TestCase):

    def test_basic_attributes(self):
        dt = date(2002, 3, 1)
        dt_2 = cpython_date(2002, 3, 1)
        self.assertEqual(dt.year, dt_2.year)
        self.assertEqual(dt.month, dt_2.month)
        self.assertEqual(dt.day, dt_2.day)

if __name__ == '__main__':
    unittest.main()