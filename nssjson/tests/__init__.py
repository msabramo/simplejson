from __future__ import absolute_import
import unittest
import doctest
import sys


def additional_tests(suite=None):
    import nssjson
    import nssjson.encoder
    import nssjson.decoder
    if suite is None:
        suite = unittest.TestSuite()
    for mod in (nssjson, nssjson.encoder, nssjson.decoder):
        suite.addTest(doctest.DocTestSuite(mod))
    suite.addTest(doctest.DocFileSuite('../../index.rst'))
    suite.addTest(doctest.DocFileSuite('../../README.rst'))
    return suite


def all_tests_suite():
    suite = unittest.TestLoader().loadTestsFromNames([
        'nssjson.tests.test_bigint_as_string',
        'nssjson.tests.test_check_circular',
        'nssjson.tests.test_decode',
        'nssjson.tests.test_default',
        'nssjson.tests.test_dump',
        'nssjson.tests.test_encode_basestring_ascii',
        'nssjson.tests.test_encode_for_html',
        'nssjson.tests.test_errors',
        'nssjson.tests.test_fail',
        'nssjson.tests.test_float',
        'nssjson.tests.test_indent',
        'nssjson.tests.test_pass1',
        'nssjson.tests.test_pass2',
        'nssjson.tests.test_pass3',
        'nssjson.tests.test_recursion',
        'nssjson.tests.test_scanstring',
        'nssjson.tests.test_separators',
        'nssjson.tests.test_speedups',
        'nssjson.tests.test_unicode',
        'nssjson.tests.test_decimal',
        'nssjson.tests.test_datetime',
        'nssjson.tests.test_tuple',
        'nssjson.tests.test_namedtuple',
        'nssjson.tests.test_tool',
        'nssjson.tests.test_for_json',
    ])
    return additional_tests(suite)


def main():
    import nssjson

    runner = unittest.TextTestRunner(verbosity=1 + sys.argv.count('-v'))

    first_run = runner.run(all_tests_suite()).wasSuccessful()
    if nssjson._import_c_make_encoder() is not None:
        nssjson._toggle_speedups(False)
        runner.stream.write('Pure Python, without C speedups...\n')
        second_run = runner.run(all_tests_suite()).wasSuccessful()
        nssjson._toggle_speedups(True)
    else:
        second_run = True
    raise SystemExit(not (first_run and second_run))


if __name__ == '__main__':
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    main()
