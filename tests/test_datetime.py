import sys
import unittest
from test_date import TestDate
# CPython standard implementation
from datetime import datetime as cpython_datetime
from datetime import MINYEAR, MAXYEAR
# CircuitPython subset implementation
sys.path.append("..")
from adafruit_datetime import datetime as cpy_datetime
from adafruit_datetime import timedelta
from adafruit_datetime import tzinfo

# TZinfo test
class FixedOffset(tzinfo):

    def __init__(self, offset, name, dstoffset=42):
        if isinstance(offset, int):
            offset = timedelta(minutes=offset)
        if isinstance(dstoffset, int):
            dstoffset = timedelta(minutes=dstoffset)
        self.__offset = offset
        self.__name = name
        self.__dstoffset = dstoffset
    def __repr__(self):
        return self.__name.lower()
    def utcoffset(self, dt):
        return self.__offset
    def tzname(self, dt):
        return self.__name
    def dst(self, dt):
        return self.__dstoffset

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

    def test_basic_attributes_nonzero(self):
        # Make sure all attributes are non-zero so bugs in
        # bit-shifting access show up.
        dt = self.theclass(2002, 3, 1, 12, 59, 59, 8000)
        self.assertEqual(dt.year, 2002)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 1)
        self.assertEqual(dt.hour, 12)
        self.assertEqual(dt.minute, 59)
        self.assertEqual(dt.second, 59)
        self.assertEqual(dt.microsecond, 8000)

    @unittest.skip("issue with startswith and ada lib.")
    def test_roundtrip(self):
        for dt in (self.theclass(1, 2, 3, 4, 5, 6, 7),
                   self.theclass.now()):
            # Verify dt -> string -> datetime identity.
            s = repr(dt)
            self.assertTrue(s.startswith('datetime.'))
            s = s[9:]
            dt2 = eval(s)
            self.assertEqual(dt, dt2)

            # Verify identity via reconstructing from pieces.
            dt2 = self.theclass(dt.year, dt.month, dt.day,
                                dt.hour, dt.minute, dt.second,
                                dt.microsecond)
            self.assertEqual(dt, dt2)

    @unittest.skip("isoformat not implemented")
    def test_isoformat(self):
        t = self.theclass(1, 2, 3, 4, 5, 1, 123)
        self.assertEqual(t.isoformat(),    "0001-02-03T04:05:01.000123")
        self.assertEqual(t.isoformat('T'), "0001-02-03T04:05:01.000123")
        self.assertEqual(t.isoformat(' '), "0001-02-03 04:05:01.000123")
        self.assertEqual(t.isoformat('\x00'), "0001-02-03\x0004:05:01.000123")
        # bpo-34482: Check that surrogates are handled properly.
        self.assertEqual(t.isoformat('\ud800'),
                         "0001-02-03\ud80004:05:01.000123")
        self.assertEqual(t.isoformat(timespec='hours'), "0001-02-03T04")
        self.assertEqual(t.isoformat(timespec='minutes'), "0001-02-03T04:05")
        self.assertEqual(t.isoformat(timespec='seconds'), "0001-02-03T04:05:01")
        self.assertEqual(t.isoformat(timespec='milliseconds'), "0001-02-03T04:05:01.000")
        self.assertEqual(t.isoformat(timespec='microseconds'), "0001-02-03T04:05:01.000123")
        self.assertEqual(t.isoformat(timespec='auto'), "0001-02-03T04:05:01.000123")
        self.assertEqual(t.isoformat(sep=' ', timespec='minutes'), "0001-02-03 04:05")
        self.assertRaises(ValueError, t.isoformat, timespec='foo')
        # bpo-34482: Check that surrogates are handled properly.
        self.assertRaises(ValueError, t.isoformat, timespec='\ud800')
        # str is ISO format with the separator forced to a blank.
        self.assertEqual(str(t), "0001-02-03 04:05:01.000123")

        t = self.theclass(1, 2, 3, 4, 5, 1, 999500, tzinfo=timezone.utc)
        self.assertEqual(t.isoformat(timespec='milliseconds'), "0001-02-03T04:05:01.999+00:00")

        t = self.theclass(1, 2, 3, 4, 5, 1, 999500)
        self.assertEqual(t.isoformat(timespec='milliseconds'), "0001-02-03T04:05:01.999")

        t = self.theclass(1, 2, 3, 4, 5, 1)
        self.assertEqual(t.isoformat(timespec='auto'), "0001-02-03T04:05:01")
        self.assertEqual(t.isoformat(timespec='milliseconds'), "0001-02-03T04:05:01.000")
        self.assertEqual(t.isoformat(timespec='microseconds'), "0001-02-03T04:05:01.000000")

        t = self.theclass(2, 3, 2)
        self.assertEqual(t.isoformat(),    "0002-03-02T00:00:00")
        self.assertEqual(t.isoformat('T'), "0002-03-02T00:00:00")
        self.assertEqual(t.isoformat(' '), "0002-03-02 00:00:00")
        # str is ISO format with the separator forced to a blank.
        self.assertEqual(str(t), "0002-03-02 00:00:00")
        # ISO format with timezone
        tz = FixedOffset(timedelta(seconds=16), 'XXX')
        t = self.theclass(2, 3, 2, tzinfo=tz)
        self.assertEqual(t.isoformat(), "0002-03-02T00:00:00+00:00:16")

    @unittest.skip("isoformat not implemented.")
    def test_isoformat_timezone(self):
        tzoffsets = [
            ('05:00', timedelta(hours=5)),
            ('02:00', timedelta(hours=2)),
            ('06:27', timedelta(hours=6, minutes=27)),
            ('12:32:30', timedelta(hours=12, minutes=32, seconds=30)),
            ('02:04:09.123456', timedelta(hours=2, minutes=4, seconds=9, microseconds=123456))
        ]

        tzinfos = [
            ('', None),
            ('+00:00', timezone.utc),
            ('+00:00', timezone(timedelta(0))),
        ]

        tzinfos += [
            (prefix + expected, timezone(sign * td))
            for expected, td in tzoffsets
            for prefix, sign in [('-', -1), ('+', 1)]
        ]

        dt_base = self.theclass(2016, 4, 1, 12, 37, 9)
        exp_base = '2016-04-01T12:37:09'

        for exp_tz, tzi in tzinfos:
            dt = dt_base.replace(tzinfo=tzi)
            exp = exp_base + exp_tz
            with self.subTest(tzi=tzi):
                assert dt.isoformat() == exp

    def test_format(self):
        dt = self.theclass(2007, 9, 10, 4, 5, 1, 123)
        self.assertEqual(dt.__format__(''), str(dt))

        with self.assertRaisesRegex(TypeError, 'must be str, not int'):
            dt.__format__(123)

        # check that a derived class's __str__() gets called
        class A(self.theclass):
            def __str__(self):
                return 'A'
        a = A(2007, 9, 10, 4, 5, 1, 123)
        self.assertEqual(a.__format__(''), 'A')

        # check that a derived class's strftime gets called
        class B(self.theclass):
            def strftime(self, format_spec):
                return 'B'
        b = B(2007, 9, 10, 4, 5, 1, 123)
        self.assertEqual(b.__format__(''), str(dt))

        for fmt in ["m:%m d:%d y:%y",
                    "m:%m d:%d y:%y H:%H M:%M S:%S",
                    "%z %Z",
                    ]:
            self.assertEqual(dt.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(a.__format__(fmt), dt.strftime(fmt))
            self.assertEqual(b.__format__(fmt), 'B')

    @unittest.skip("ctime not implemented")
    def test_more_ctime(self):
        # Test fields that TestDate doesn't touch.
        import time

        t = self.theclass(2002, 3, 2, 18, 3, 5, 123)
        self.assertEqual(t.ctime(), "Sat Mar  2 18:03:05 2002")
        # Oops!  The next line fails on Win2K under MSVC 6, so it's commented
        # out.  The difference is that t.ctime() produces " 2" for the day,
        # but platform ctime() produces "02" for the day.  According to
        # C99, t.ctime() is correct here.
        # self.assertEqual(t.ctime(), time.ctime(time.mktime(t.timetuple())))

        # So test a case where that difference doesn't matter.
        t = self.theclass(2002, 3, 22, 18, 3, 5, 123)
        self.assertEqual(t.ctime(), time.ctime(time.mktime(t.timetuple())))

    def test_tz_independent_comparing(self):
        dt1 = self.theclass(2002, 3, 1, 9, 0, 0)
        dt2 = self.theclass(2002, 3, 1, 10, 0, 0)
        dt3 = self.theclass(2002, 3, 1, 9, 0, 0)
        self.assertEqual(dt1, dt3)
        self.assertTrue(dt2 > dt3)

        # Make sure comparison doesn't forget microseconds, and isn't done
        # via comparing a float timestamp (an IEEE double doesn't have enough
        # precision to span microsecond resolution across years 1 through 9999,
        # so comparing via timestamp necessarily calls some distinct values
        # equal).
        dt1 = self.theclass(MAXYEAR, 12, 31, 23, 59, 59, 999998)
        us = timedelta(microseconds=1)
        dt2 = dt1 + us
        self.assertEqual(dt2 - dt1, us)
        self.assertTrue(dt1 < dt2)

    @unittest.skip("not implemented - strftime")
    def test_strftime_with_bad_tzname_replace(self):
        # verify ok if tzinfo.tzname().replace() returns a non-string
        class MyTzInfo(FixedOffset):
            def tzname(self, dt):
                class MyStr(str):
                    def replace(self, *args):
                        return None
                return MyStr('name')
        t = self.theclass(2005, 3, 2, 0, 0, 0, 0, MyTzInfo(3, 'name'))
        self.assertRaises(TypeError, t.strftime, '%Z')

    def test_bad_constructor_arguments(self):
        # bad years
        self.theclass(MINYEAR, 1, 1)  # no exception
        self.theclass(MAXYEAR, 1, 1)  # no exception
        self.assertRaises(ValueError, self.theclass, MINYEAR-1, 1, 1)
        self.assertRaises(ValueError, self.theclass, MAXYEAR+1, 1, 1)
        # bad months
        self.theclass(2000, 1, 1)    # no exception
        self.theclass(2000, 12, 1)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 0, 1)
        self.assertRaises(ValueError, self.theclass, 2000, 13, 1)
        # bad days
        self.theclass(2000, 2, 29)   # no exception
        self.theclass(2004, 2, 29)   # no exception
        self.theclass(2400, 2, 29)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 2, 30)
        self.assertRaises(ValueError, self.theclass, 2001, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2100, 2, 29)
        self.assertRaises(ValueError, self.theclass, 1900, 2, 29)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 0)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 32)
        # bad hours
        self.theclass(2000, 1, 31, 0)    # no exception
        self.theclass(2000, 1, 31, 23)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, -1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 24)
        # bad minutes
        self.theclass(2000, 1, 31, 23, 0)    # no exception
        self.theclass(2000, 1, 31, 23, 59)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, -1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 60)
        # bad seconds
        self.theclass(2000, 1, 31, 23, 59, 0)    # no exception
        self.theclass(2000, 1, 31, 23, 59, 59)   # no exception
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 59, -1)
        self.assertRaises(ValueError, self.theclass, 2000, 1, 31, 23, 59, 60)
        # bad microseconds
        self.theclass(2000, 1, 31, 23, 59, 59, 0)    # no exception
        self.theclass(2000, 1, 31, 23, 59, 59, 999999)   # no exception
        self.assertRaises(ValueError, self.theclass,
                          2000, 1, 31, 23, 59, 59, -1)
        self.assertRaises(ValueError, self.theclass,
                          2000, 1, 31, 23, 59, 59,
                          1000000)
        # bad fold
        self.assertRaises(ValueError, self.theclass,
                          2000, 1, 31, fold=-1)
        self.assertRaises(ValueError, self.theclass,
                          2000, 1, 31, fold=2)
        # Positional fold:
        self.assertRaises(TypeError, self.theclass,
                          2000, 1, 31, 23, 59, 59, 0, None, 1)


    def test_hash_equality(self):
        d = self.theclass(2000, 12, 31, 23, 30, 17)
        e = self.theclass(2000, 12, 31, 23, 30, 17)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

        d = self.theclass(2001,  1,  1,  0,  5, 17)
        e = self.theclass(2001,  1,  1,  0,  5, 17)
        self.assertEqual(d, e)
        self.assertEqual(hash(d), hash(e))

        dic = {d: 1}
        dic[e] = 2
        self.assertEqual(len(dic), 1)
        self.assertEqual(dic[d], 2)
        self.assertEqual(dic[e], 2)

    def test_computations(self):
        a = self.theclass(2002, 1, 31)
        b = self.theclass(1956, 1, 31)
        diff = a-b
        self.assertEqual(diff.days, 46*365 + len(range(1956, 2002, 4)))
        self.assertEqual(diff.seconds, 0)
        self.assertEqual(diff.microseconds, 0)
        a = self.theclass(2002, 3, 2, 17, 6)
        millisec = timedelta(0, 0, 1000)
        hour = timedelta(0, 3600)
        day = timedelta(1)
        week = timedelta(7)
        self.assertEqual(a + hour, self.theclass(2002, 3, 2, 18, 6))
        self.assertEqual(hour + a, self.theclass(2002, 3, 2, 18, 6))
        self.assertEqual(a + 10*hour, self.theclass(2002, 3, 3, 3, 6))
        self.assertEqual(a - hour, self.theclass(2002, 3, 2, 16, 6))
        self.assertEqual(-hour + a, self.theclass(2002, 3, 2, 16, 6))
        self.assertEqual(a - hour, a + -hour)
        self.assertEqual(a - 20*hour, self.theclass(2002, 3, 1, 21, 6))
        self.assertEqual(a + day, self.theclass(2002, 3, 3, 17, 6))
        self.assertEqual(a - day, self.theclass(2002, 3, 1, 17, 6))
        self.assertEqual(a + week, self.theclass(2002, 3, 9, 17, 6))
        self.assertEqual(a - week, self.theclass(2002, 2, 23, 17, 6))
        self.assertEqual(a + 52*week, self.theclass(2003, 3, 1, 17, 6))
        self.assertEqual(a - 52*week, self.theclass(2001, 3, 3, 17, 6))
        self.assertEqual((a + week) - a, week)
        self.assertEqual((a + day) - a, day)
        self.assertEqual((a + hour) - a, hour)
        self.assertEqual((a + millisec) - a, millisec)
        self.assertEqual((a - week) - a, -week)
        self.assertEqual((a - day) - a, -day)
        self.assertEqual((a - hour) - a, -hour)
        self.assertEqual((a - millisec) - a, -millisec)
        self.assertEqual(a - (a + week), -week)
        self.assertEqual(a - (a + day), -day)
        self.assertEqual(a - (a + hour), -hour)
        self.assertEqual(a - (a + millisec), -millisec)
        self.assertEqual(a - (a - week), week)
        self.assertEqual(a - (a - day), day)
        self.assertEqual(a - (a - hour), hour)
        self.assertEqual(a - (a - millisec), millisec)
        self.assertEqual(a + (week + day + hour + millisec),
                         self.theclass(2002, 3, 10, 18, 6, 0, 1000))
        self.assertEqual(a + (week + day + hour + millisec),
                         (((a + week) + day) + hour) + millisec)
        self.assertEqual(a - (week + day + hour + millisec),
                         self.theclass(2002, 2, 22, 16, 5, 59, 999000))
        self.assertEqual(a - (week + day + hour + millisec),
                         (((a - week) - day) - hour) - millisec)
        # Add/sub ints or floats should be illegal
        for i in 1, 1.0:
            self.assertRaises(TypeError, lambda: a+i)
            self.assertRaises(TypeError, lambda: a-i)
            self.assertRaises(TypeError, lambda: i+a)
            self.assertRaises(TypeError, lambda: i-a)

        # delta - datetime is senseless.
        self.assertRaises(TypeError, lambda: day - a)
        # mixing datetime and (delta or datetime) via * or // is senseless
        self.assertRaises(TypeError, lambda: day * a)
        self.assertRaises(TypeError, lambda: a * day)
        self.assertRaises(TypeError, lambda: day // a)
        self.assertRaises(TypeError, lambda: a // day)
        self.assertRaises(TypeError, lambda: a * a)
        self.assertRaises(TypeError, lambda: a // a)
        # datetime + datetime is senseless
        self.assertRaises(TypeError, lambda: a + a)


    def test_more_compare(self):
        # The test_compare() inherited from TestDate covers the error cases.
        # We just want to test lexicographic ordering on the members datetime
        # has that date lacks.
        args = [2000, 11, 29, 20, 58, 16, 999998]
        t1 = self.theclass(*args)
        t2 = self.theclass(*args)
        self.assertEqual(t1, t2)
        self.assertTrue(t1 <= t2)
        self.assertTrue(t1 >= t2)
        self.assertFalse(t1 != t2)
        self.assertFalse(t1 < t2)
        self.assertFalse(t1 > t2)

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
            self.assertFalse(t1 == t2)
            self.assertFalse(t2 == t1)
            self.assertFalse(t1 > t2)
            self.assertFalse(t2 < t1)
            self.assertFalse(t1 >= t2)
            self.assertFalse(t2 <= t1)

    # A helper for timestamp constructor tests.
    def verify_field_equality(self, expected, got):
        self.assertEqual(expected.tm_year, got.year)
        self.assertEqual(expected.tm_mon, got.month)
        self.assertEqual(expected.tm_mday, got.day)
        self.assertEqual(expected.tm_hour, got.hour)
        self.assertEqual(expected.tm_min, got.minute)
        self.assertEqual(expected.tm_sec, got.second)

    def test_fromtimestamp(self):
        import time

        ts = time.time()
        expected = time.localtime(ts)
        got = self.theclass.fromtimestamp(ts)
        print(expected, got)
        self.verify_field_equality(expected, got)

    def test_utcfromtimestamp(self):
        import time

        ts = time.time()
        expected = time.gmtime(ts)
        got = self.theclass.utcfromtimestamp(ts)
        self.verify_field_equality(expected, got)
