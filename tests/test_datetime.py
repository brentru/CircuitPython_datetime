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
        dt = self.theclass_cpython(2002, 3, 1, 12, 0)
        self.assertEqual(dt.year, 2002)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)
        self.assertEqual(dt.microsecond, 0)