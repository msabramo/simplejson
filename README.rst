=========
 nssjson
=========

JSON encoder/decoder for Python
===============================

nssjson is a (not so) simple, fast, complete, correct and extensible `JSON <http://json.org>`_
encoder and decoder for Python 2.5+ and Python 3.3+.  It is pure Python code with no
dependencies, but includes an optional C extension for a serious speed boost.

nssjson__ is a fork of simplejson__ that fulfills my need of having a good performance JSON
encoder/decoder able to handle also Python's datetime, even if with an admittedly non-standard
and faulty heuristic that was `not considered`__ within the scope of the original product.

Practically, the difference is that, out of the box, you have:

.. code-block:: python

    >>> import datetime
    >>> import nssjson
    >>> now = datetime.datetime.now()
    >>> nssjson.loads(
    ...     nssjson.dumps(now, iso_datetime=True),
    ...     iso_datetime=True) == now
    True

__ https://github.com/lelit/nssjson
__ https://github.com/simplejson/simplejson
__ https://github.com/simplejson/simplejson/pull/89
