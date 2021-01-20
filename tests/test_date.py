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

    # TODO: Test this when timedelta is added in
    @unittest.skip("Skip for CircuitPython - timedelta() not yet implemented.")
    def test_today(self):
        import time
        # We claim that today() is like fromtimestamp(time.time()), so
        # prove it.
        for dummy in range(3):
            today = self.theclass.today()
            ts = time.time()
            todayagain = self.theclass.fromtimestamp(ts)
            if today == todayagain:
                break
            # There are several legit reasons that could fail:
            # 1. It recently became midnight, between the today() and the
            #    time() calls.
            # 2. The platform time() has such fine resolution that we'll
            #    never get the same value twice.
            # 3. The platform time() has poor resolution, and we just
            #    happened to call today() right before a resolution quantum
            #    boundary.
            # 4. The system clock got fiddled between calls.
            # In any case, wait a little while and try again.
            time.sleep(0.1)

        # It worked or it didn't.  If it didn't, assume it's reason #2, and
        # let the test pass if they're within half a second of each other.
        self.assertTrue(today == todayagain or
                        abs(todayagain - today) < timedelta(seconds=0.5))

    def test_weekday(self):
        for i in range(7):
            # March 4, 2002 is a Monday
            self.assertEqual(cpy_date(2002, 3, 4+i).weekday(), cpython_date(2002, 3, 4+i).weekday())
            self.assertEqual(cpy_date(2002, 3, 4+i).isoweekday(), cpython_date(2002, 3, 4+i).isoweekday())
            # January 2, 1956 is a Monday
            self.assertEqual(cpy_date(1956, 1, 2+i).weekday(), cpython_date(1956, 1, 2+i).weekday())
            self.assertEqual(cpy_date(1956, 1, 2+i).isoweekday(), cpython_date(1956, 1, 2+i).isoweekday())

    @unittest.skip("Skip for CircuitPython - isocalendar() not implemented for date objects.")
    def test_isocalendar(self):
        # Check examples from
        # http://www.phys.uu.nl/~vgent/calendar/isocalendar.htm
        for i in range(7):
            d = self.theclass(2003, 12, 22+i)
            self.assertEqual(d.isocalendar(), (2003, 52, i+1))
            d = self.theclass(2003, 12, 29) + timedelta(i)
            self.assertEqual(d.isocalendar(), (2004, 1, i+1))
            d = self.theclass(2004, 1, 5+i)
            self.assertEqual(d.isocalendar(), (2004, 2, i+1))
            d = self.theclass(2009, 12, 21+i)
            self.assertEqual(d.isocalendar(), (2009, 52, i+1))
            d = self.theclass(2009, 12, 28) + timedelta(i)
            self.assertEqual(d.isocalendar(), (2009, 53, i+1))
            d = self.theclass(2010, 1, 4+i)
            self.assertEqual(d.isocalendar(), (2010, 1, i+1))

    def test_isoformat(self):
        # test isoformat against expected and cpython equiv.
        t = cpy_date(2, 3, 2)
        t2 = cpython_date(2, 3, 2)
        self.assertEqual(t.isoformat(), "0002-03-02")
        self.assertEqual(t.isoformat(), t2.isoformat())

    @unittest.skip("Skip for CircuitPython - ctime() not implemented for date objects.")
    def test_ctime(self):
        t = self.theclass(2002, 3, 2)
        self.assertEqual(t.ctime(), "Sat Mar  2 00:00:00 2002")

    @unittest.skip("Skip for CircuitPython - strftime() not implemented for date objects.")
    def test_strftime(self):
        t = self.theclass(2005, 3, 2)
        self.assertEqual(t.strftime("m:%m d:%d y:%y"), "m:03 d:02 y:05")
        self.assertEqual(t.strftime(""), "") # SF bug #761337
#        self.assertEqual(t.strftime('x'*1000), 'x'*1000) # SF bug #1556784

        self.assertRaises(TypeError, t.strftime) # needs an arg
        self.assertRaises(TypeError, t.strftime, "one", "two") # too many args
        self.assertRaises(TypeError, t.strftime, 42) # arg wrong type

        # test that unicode input is allowed (issue 2782)
        self.assertEqual(t.strftime("%m"), "03")

        # A naive object replaces %z and %Z w/ empty strings.
        self.assertEqual(t.strftime("'%z' '%Z'"), "'' ''")

        #make sure that invalid format specifiers are handled correctly
        #self.assertRaises(ValueError, t.strftime, "%e")
        #self.assertRaises(ValueError, t.strftime, "%")
        #self.assertRaises(ValueError, t.strftime, "%#")

        #oh well, some systems just ignore those invalid ones.
        #at least, excercise them to make sure that no crashes
        #are generated
        for f in ["%e", "%", "%#"]:
            try:
                t.strftime(f)
            except ValueError:
                pass

        #check that this standard extension works
        t.strftime("%f")

    def test_format(self):
        dt = cpy_date(2007, 9, 10)
        self.assertEqual(dt.__format__(''), str(dt))

        # check that a derived class's __str__() gets called
        class A(cpy_date):
            def __str__(self):
                return 'A'
        a = A(2007, 9, 10)
        self.assertEqual(a.__format__(''), 'A')

        # check that a derived class's strftime gets called
        class B(cpy_date):
            def strftime(self, format_spec):
                return 'B'
        b = B(2007, 9, 10)
        self.assertEqual(b.__format__(''), str(dt))

        # date strftime not implemented in CircuitPython, skip
        """for fmt in ["m:%m d:%d y:%y",
                    "m:%m d:%d y:%y H:%H M:%M S:%S",
                    "%z %Z",
                    ]:
            self.assertEqual(dt.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(a.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(b.__format__(fmt), 'B')"""


if __name__ == '__main__':
    unittest.main()