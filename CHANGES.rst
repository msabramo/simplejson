Changes
-------

0.4 (2014-06-28)
~~~~~~~~~~~~~~~~

* Complete the fix against negative index parameter to raw_decode()

* Fix C encoder initialization

* Catch invalid item_sort_key argument to C encoder


0.3 (2014-04-16)
~~~~~~~~~~~~~~~~

* Update version in nssjson/__init__.py at release time

* Catch negative index parameter to the C scan_once() function, mimicking
  http://hg.python.org/cpython/rev/ef52ae167555


0.2 (2014-03-22)
~~~~~~~~~~~~~~~~

* Remove dead code noticed by Anatoly Techtonik

* Use an interned instance of the UTC timezone instead of passing it as an argument to
  function/constructors


0.1 (2014-03-19)
~~~~~~~~~~~~~~~~

* Fork of simplejson 3.3.3

* Add support for Python datetimes, dates and times
  (see https://github.com/simplejson/simplejson/issues/86 and
  https://github.com/simplejson/simplejson/pull/89)

* Fix compatibility with Python 3.4 unittests
