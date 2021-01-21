import sys
import unittest
import time
# CPython standard implementation
from datetime import time as cpython_time
# CircuitPython subset implementation
sys.path.append("..")
from adafruit_datetime import time as cpy_time

# TODO: This should be shared
# An arbitrary collection of objects of non-datetime types, for testing
# mixed-type comparisons.
OTHERSTUFF = (10, 34.5, "abc", {}, [], ())

#############################################################################
# Base class for testing a particular aspect of timedelta, time, date and
# datetime comparisons.
# TODO: This may need to get moved and imported

class HarmlessMixedComparison:
    # Test that __eq__ and __ne__ don't complain for mixed-type comparisons.

    # Subclasses must define 'theclass', and theclass(1, 1, 1) must be a
    # legit constructor.

    def test_harmless_mixed_comparison(self):
        me = self.theclass(1, 1, 1)

        self.assertFalse(me == ())
        self.assertTrue(me != ())
        self.assertFalse(() == me)
        self.assertTrue(() != me)

        self.assertIn(me, [1, 20, [], me])
        self.assertIn([], [me, 1, 20, []])

    def test_harmful_mixed_comparison(self):
        me = self.theclass(1, 1, 1)

        self.assertRaises(TypeError, lambda: me < ())
        self.assertRaises(TypeError, lambda: me <= ())
        self.assertRaises(TypeError, lambda: me > ())
        self.assertRaises(TypeError, lambda: me >= ())

        self.assertRaises(TypeError, lambda: () < me)
        self.assertRaises(TypeError, lambda: () <= me)
        self.assertRaises(TypeError, lambda: () > me)
        self.assertRaises(TypeError, lambda: () >= me)

class TestTime(HarmlessMixedComparison, unittest.TestCase):

    theclass = cpy_time
    theclass_cpython = cpython_time

    def test_basic_attributes(self):
        t = self.theclass(12, 0)
        t2 = self.theclass_cpython(12, 0)
        # Check adafruit_datetime module
        self.assertEqual(t.hour, 12)
        self.assertEqual(t.minute, 0)
        self.assertEqual(t.second, 0)
        self.assertEqual(t.microsecond, 0)
        # Validate against CPython datetime module
        self.assertEqual(t.hour, t2.hour)
        self.assertEqual(t.minute, t2.minute)
        self.assertEqual(t.second, t2.second)
        self.assertEqual(t.microsecond, t2.microsecond)

    def test_basic_attributes_nonzero(self):
        # Make sure all attributes are non-zero so bugs in
        # bit-shifting access show up.
        t = self.theclass(12, 59, 59, 8000)
        t2 = self.theclass_cpython(12, 59, 59, 8000)
        # Check adafruit_datetime module
        self.assertEqual(t.hour, 12)
        self.assertEqual(t.minute, 59)
        self.assertEqual(t.second, 59)
        self.assertEqual(t.microsecond, 8000)
        # Validate against CPython datetime module
        self.assertEqual(t.hour, t2.hour)
        self.assertEqual(t.minute, t2.minute)
        self.assertEqual(t.second, t2.second)
        self.assertEqual(t.microsecond, t2.microsecond)

    def test_comparing(self):
        args = [1, 2, 3, 4]
        t1 = self.theclass(*args)
        t2 = self.theclass(*args)
        print(t1, t2)
        self.assertEqual(t1, t2)
        self.assertTrue(t1 <= t2)
        self.assertTrue(t1 >= t2)
        self.assertTrue(not t1 != t2)
        self.assertTrue(not t1 < t2)
        self.assertTrue(not t1 > t2)

        for i in range(len(args)):
            newargs = args[:]
            newargs[i] = args[i] + 1
            t2 = self.theclass(*newargs)   # this is larger than t1
            self.assertTrue(t1 < t2)
            self.assertTrue(t2 > t1)
            self.assertTrue(t1 <= t2)
            self.assertTrue(t2 >= t1)
            self.assertTrue(t1 != t2)
            self.assertTrue(t2 != t1)
            self.assertTrue(not t1 == t2)
            self.assertTrue(not t2 == t1)
            self.assertTrue(not t1 > t2)
            self.assertTrue(not t2 < t1)
            self.assertTrue(not t1 >= t2)
            self.assertTrue(not t2 <= t1)

        for badarg in OTHERSTUFF:
            self.assertEqual(t1 == badarg, False)
            self.assertEqual(t1 != badarg, True)
            self.assertEqual(badarg == t1, False)
            self.assertEqual(badarg != t1, True)

            self.assertRaises(TypeError, lambda: t1 <= badarg)
            self.assertRaises(TypeError, lambda: t1 < badarg)
            self.assertRaises(TypeError, lambda: t1 > badarg)
            self.assertRaises(TypeError, lambda: t1 >= badarg)
            self.assertRaises(TypeError, lambda: badarg <= t1)
            self.assertRaises(TypeError, lambda: badarg < t1)
            self.assertRaises(TypeError, lambda: badarg > t1)
            self.assertRaises(TypeError, lambda: badarg >= t1)
