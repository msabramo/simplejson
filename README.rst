nssjson is a (not so) simple, fast, complete, correct and extensible JSON <http://json.org>
encoder and decoder for Python 2.5+ and Python 3.3+.  It is pure Python code with no
dependencies, but includes an optional C extension for a serious speed boost.

nssjson_ is a fork of simplejson_ that fulfills my need of having a good performance JSON
encoder/decoder able to handle also Python's datetime, even if with an admittedly non-standard
and faulty heuristic that was not considered within the scope\ [#]_ of the original product.

Practically, the difference is that, out of the box, you have::

    >>> import datetime
    >>> import nssjson
    >>> now = datetime.datetime.now()
    >>> nssjson.loads(nssjson.dumps(now, iso_datetime=True), iso_datetime=True) == now
    True

.. _nssjson: https://github.com/lelit/nssjson
.. _simplejson: https://github.com/simplejson/simplejson
.. [#] See https://github.com/simplejson/simplejson/issues/86 and
       https://github.com/simplejson/simplejson/pull/89
