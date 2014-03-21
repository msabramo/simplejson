import datetime
from datetime import (
    datetime as DateTime,
    date as Date,
    time as Time,
    timedelta as TimeDelta,
    tzinfo,
)
from unittest import TestCase

import nssjson as json
from nssjson.compat import StringIO, reload_module, utc


class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset, name):
        self.__offset = TimeDelta(minutes=offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return TimeDelta(0)


class AbstractDatetimeTestSuite(object):
    VALUES = ()

    def dumps(self, obj, **kw):
        sio = StringIO()
        json.dump(obj, sio, **kw)
        res = json.dumps(obj, **kw)
        self.assertEqual(res, sio.getvalue())
        return res

    def loads(self, s, **kw):
        sio = StringIO(s)
        res = json.loads(s, **kw)
        self.assertEqual(res, json.load(sio, **kw))
        return res

    def test_decode(self):
        for d in self.VALUES:
            self.assertEqual(self.loads('"%s"' % d.isoformat(), iso_datetime=True), d)

    def test_stringify_key(self):
        for d in self.VALUES:
            v = {d: d}
            self.assertEqual(
                self.loads(
                    self.dumps(v, iso_datetime=True), iso_datetime=True),
                v)

    def test_roundtrip(self):
        for d in self.VALUES:
            for v in [d, [d], {'': d}]:
                self.assertEqual(
                    self.loads(
                        self.dumps(v, iso_datetime=True), iso_datetime=True),
                    v)

    def test_defaults(self):
        d = self.VALUES[0]
        self.assertRaises(TypeError, json.dumps, d)
        self.assertRaises(TypeError, json.dumps, d, iso_datetime=False)
        self.assertRaises(TypeError, json.dump, d, StringIO())
        self.assertRaises(TypeError, json.dump, d, StringIO(), iso_datetime=False)


class TestDatetime(TestCase, AbstractDatetimeTestSuite):
    VALUES = (DateTime(2014, 3, 18, 10, 10, 0),
              DateTime(1900, 1, 1, 0, 0, 0),
              DateTime(2014, 3, 18, 10, 10, 1, 1),
              DateTime(2014, 3, 18, 10, 10, 1, 100),
              DateTime(2014, 3, 18, 10, 10, 1, 10000),
              DateTime(2014, 3, 18, 10, 10, 1, 100000))

    def test_encode(self):
        self.assertEqual(json.dumps(list(self.VALUES), iso_datetime=True),
                         str(["%s" % d.isoformat() for d in self.VALUES]).replace("'", '"'))
        for d in self.VALUES:
            self.assertEqual(self.dumps(d, iso_datetime=True), '"%s"' % d.isoformat())

    def test_reload(self):
        # Simulate a subinterpreter that reloads the Python modules but not
        # the C code https://github.com/simplejson/simplejson/issues/34
        global DateTime
        DateTime = reload_module(datetime).datetime
        import nssjson.encoder
        nssjson.encoder.datetime = DateTime
        self.test_roundtrip()


class TestTZADateTeime(TestCase):
    MOFFSET = 120
    TST = FixedOffset(120, "TST")
    VALUES = (DateTime(2014, 3, 18, 10, 10, 0, 0, TST),
              DateTime(1900, 1, 1, 0, 0, 0, 0, TST),
              DateTime(2014, 3, 18, 10, 10, 1, 1, TST),
              DateTime(2014, 3, 18, 10, 10, 1, 100, TST),
              DateTime(2014, 3, 18, 10, 10, 1, 10000, TST),
              DateTime(2014, 3, 18, 10, 10, 1, 100000, TST))

    def test_encode(self):
        ofs = TimeDelta(minutes=self.MOFFSET)
        for d in self.VALUES:
            self.assertEqual(json.dumps(d, iso_datetime=True,),
                             '"%s"' % (d.isoformat().split('+')[0]))
            self.assertEqual(json.dumps(d, iso_datetime=True, utc_datetime=True),
                             '"%sZ"' % (d - ofs).isoformat().split('+')[0])


class TestDate(TestCase, AbstractDatetimeTestSuite):
    VALUES = (Date(2014, 3, 18), Date(1900, 1, 1), Date(1, 1, 1))

    def test_encode(self):
        self.assertEqual(json.dumps(list(self.VALUES), iso_datetime=True),
                         str(["%s" % d.isoformat() for d in self.VALUES]).replace("'", '"'))
        for d in self.VALUES:
            self.assertEqual(self.dumps(d, iso_datetime=True), '"%s"' % d.isoformat())

    def test_decode(self):
        for d in self.VALUES:
            self.assertEqual(self.loads('"%s"' % d.isoformat(), iso_datetime=True), d)

    def test_reload(self):
        # Simulate a subinterpreter that reloads the Python modules but not
        # the C code https://github.com/simplejson/simplejson/issues/34
        global Date
        Date = reload_module(datetime).date
        import nssjson.encoder
        nssjson.encoder.date = Date
        self.test_roundtrip()


class TestTime(TestCase, AbstractDatetimeTestSuite):
    VALUES = (Time(10, 10, 0), Time(0, 0, 0),
              Time(1, 1, 1, 1), Time(23, 23, 23, 999999))

    def test_encode(self):
        self.assertEqual(json.dumps(list(self.VALUES), iso_datetime=True),
                         str(["%s" % d.isoformat() for d in self.VALUES]).replace("'", '"'))
        for d in self.VALUES:
            self.assertEqual(self.dumps(d, iso_datetime=True), '"%s"' % d.isoformat())


class TestScanString(TestCase):
    def test_defaults(self):
        self.assertEqual(json.loads('"1999-01-01"'), "1999-01-01")
        self.assertEqual(json.loads('"1999-01-01"', iso_datetime=False), "1999-01-01")

    def test_scanstring(self):
        ss = json.decoder.scanstring

        self.assertEqual(ss('"1999-01-01"', 1), ('1999-01-01', 12))
        self.assertEqual(ss('"1999-01-01T01:02:03"', 1), ('1999-01-01T01:02:03', 21))
        self.assertEqual(ss('"1999-01-01T01:02:03Z"', 1), ('1999-01-01T01:02:03Z', 22))
        self.assertEqual(ss('"10:20:30"', 1), ('10:20:30', 10))

        self.assertEqual(ss('"1999-01-01"', 1, None, True, True),
                         (Date(1999, 1, 1), 12))
        self.assertEqual(ss('"1999-01-01T01:02:03"', 1, None, True, True),
                         (DateTime(1999, 1, 1, 1, 2, 3), 21))
        self.assertEqual(ss('"1999-01-01T01:02:03Z"', 1, None, True, True),
                         (DateTime(1999, 1, 1, 1, 2, 3, 0, utc), 22))
        self.assertEqual(ss('"10:20:30"', 1, None, True, True),
                         (Time(10, 20, 30), 10))
