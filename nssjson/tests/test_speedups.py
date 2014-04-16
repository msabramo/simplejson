from unittest import TestCase

from nssjson import encoder, scanner

def has_speedups():
    return encoder.c_make_encoder is not None

class TestDecode(TestCase):
    def test_make_scanner(self):
        if not has_speedups():
            return
        self.assertRaises(AttributeError, scanner.c_make_scanner, 1)

    def test_scan_once(self):
        if not has_speedups():
            return
        from nssjson import _default_decoder as dd
        self.assertRaises(ValueError, dd.scan_once, '"foo"', -1)
        self.assertRaises(ValueError, dd.scan_once, u'"foo"', -1)
        self.assertEqual(dd.scan_once('"foo"', 0), ('foo', 5))
        self.assertEqual(dd.scan_once(u'"foo"', 0), ('foo', 5))

    def test_make_encoder(self):
        if not has_speedups():
            return
        self.assertRaises(TypeError, encoder.c_make_encoder,
            None,
            "\xCD\x7D\x3D\x4E\x12\x4C\xF9\x79\xD7\x52\xBA\x82\xF2\x27\x4A\x7D\xA0\xCA\x75",
            None)
