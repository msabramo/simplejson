r"""JSON (JavaScript Object Notation) <http://json.org> is a subset of
JavaScript syntax (ECMA-262 3rd edition) used as a lightweight data
interchange format.

:mod:`nssjson` exposes an API familiar to users of the standard library
:mod:`marshal` and :mod:`pickle` modules. It is the externally maintained
version of the :mod:`json` library contained in Python 2.6, but maintains
compatibility with Python 2.4 and Python 2.5 and (currently) has
significant performance advantages, even without using the optional C
extension for speedups.

Encoding basic Python object hierarchies::

    >>> import nssjson as json
    >>> json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
    '["foo", {"bar": ["baz", null, 1.0, 2]}]'
    >>> print(json.dumps("\"foo\bar"))
    "\"foo\bar"
    >>> print(json.dumps(u'\u1234'))
    "\u1234"
    >>> print(json.dumps('\\'))
    "\\"
    >>> print(json.dumps({"c": 0, "b": 0, "a": 0}, sort_keys=True))
    {"a": 0, "b": 0, "c": 0}
    >>> from nssjson.compat import StringIO
    >>> io = StringIO()
    >>> json.dump(['streaming API'], io)
    >>> io.getvalue()
    '["streaming API"]'

Compact encoding::

    >>> import nssjson as json
    >>> obj = [1,2,3,{'4': 5, '6': 7}]
    >>> json.dumps(obj, separators=(',',':'), sort_keys=True)
    '[1,2,3,{"4":5,"6":7}]'

Pretty printing::

    >>> import nssjson as json
    >>> print(json.dumps({'4': 5, '6': 7}, sort_keys=True, indent='    '))
    {
        "4": 5,
        "6": 7
    }

Decoding JSON::

    >>> import nssjson as json
    >>> obj = [u'foo', {u'bar': [u'baz', None, 1.0, 2]}]
    >>> json.loads('["foo", {"bar":["baz", null, 1.0, 2]}]') == obj
    True
    >>> json.loads('"\\"foo\\bar"') == u'"foo\x08ar'
    True
    >>> from nssjson.compat import StringIO
    >>> io = StringIO('["streaming API"]')
    >>> json.load(io)[0] == 'streaming API'
    True

Specializing JSON object decoding::

    >>> import nssjson as json
    >>> def as_complex(dct):
    ...     if '__complex__' in dct:
    ...         return complex(dct['real'], dct['imag'])
    ...     return dct
    ...
    >>> json.loads('{"__complex__": true, "real": 1, "imag": 2}',
    ...     object_hook=as_complex)
    (1+2j)
    >>> from decimal import Decimal
    >>> json.loads('1.1', parse_float=Decimal) == Decimal('1.1')
    True

Specializing JSON object encoding::

    >>> import nssjson as json
    >>> def encode_complex(obj):
    ...     if isinstance(obj, complex):
    ...         return [obj.real, obj.imag]
    ...     raise TypeError(repr(o) + " is not JSON serializable")
    ...
    >>> json.dumps(2 + 1j, default=encode_complex)
    '[2.0, 1.0]'
    >>> json.JSONEncoder(default=encode_complex).encode(2 + 1j)
    '[2.0, 1.0]'
    >>> ''.join(json.JSONEncoder(default=encode_complex).iterencode(2 + 1j))
    '[2.0, 1.0]'


Using nssjson.tool from the shell to validate and pretty-print::

    $ echo '{"json":"obj"}' | python -m nssjson.tool
    {
        "json": "obj"
    }
    $ echo '{ 1.2:3.4}' | python -m nssjson.tool
    Expecting property name: line 1 column 3 (char 2)
"""

from __future__ import absolute_import

__version__ = '0.4'
__all__ = [
    'dump', 'dumps', 'load', 'loads',
    'JSONDecoder', 'JSONDecodeError', 'JSONEncoder',
    'OrderedDict', 'simple_first',
]

__author__ = 'Bob Ippolito <bob@redivi.com>'

from decimal import Decimal

from .scanner import JSONDecodeError
from .decoder import JSONDecoder
from .encoder import JSONEncoder, JSONEncoderForHTML

def _import_OrderedDict():
    import collections
    try:
        return collections.OrderedDict
    except AttributeError:
        from . import ordered_dict
        return ordered_dict.OrderedDict

OrderedDict = _import_OrderedDict()


def _import_c_make_encoder():
    try:
        from ._speedups import make_encoder
        return make_encoder
    except ImportError:
        return None


_default_encoder = JSONEncoder()

def dump(obj, fp, cls=None, **kw):
    """Serialize `obj` as a JSON formatted stream to `fp`.

    :param obj: the object to be serialized
    :param fp: a ``.write()``-supporting file-like object
    :keyword class cls: an alternative implementation of ``JSONEncoder``

    To use a custom ``JSONEncoder`` subclass (e.g. one that overrides the ``.default()`` method
    to serialize additional types), specify it with the `cls` kwarg.

    .. note:: You should use `default` or `for_json` instead of subclassing whenever possible.

    Additional keyword arguments are forwarded to the :class:`JSONEncoder` constructor.
    """

    settings = {}
    settings.update(JSONEncoder.SENSIBLE_DEFAULTS)
    settings.update(kw)

    # cached encoder
    if (cls is None and settings == JSONEncoder.SENSIBLE_DEFAULTS):
        iterable = _default_encoder.iterencode(obj)
    else:
        if cls is None:
            cls = JSONEncoder
        iterable = cls(**settings).iterencode(obj)
    # could accelerate with writelines in some versions of Python, at
    # a debuggability cost
    for chunk in iterable:
        fp.write(chunk)


def dumps(obj, cls=None, **kw):
    """Serialize `obj` to a JSON formatted `str`.

    :param obj: the object to be serialized
    :keyword class cls: an alternative implementation of ``JSONEncoder``
    :rtype: str
    :return: the JSON serialization of `obj`

    To use a custom ``JSONEncoder`` subclass (e.g. one that overrides the ``.default()`` method
    to serialize additional types), specify it with the `cls` kwarg.

    .. note:: You should use `default` or `for_json` instead of subclassing whenever possible.

    Additional keyword arguments are forwarded to the :class:`JSONEncoder` constructor.
    """

    settings = {}
    settings.update(JSONEncoder.SENSIBLE_DEFAULTS)
    settings.update(kw)

    # cached encoder
    if (cls is None and settings == JSONEncoder.SENSIBLE_DEFAULTS):
        return _default_encoder.encode(obj)
    if cls is None:
        cls = JSONEncoder
    return cls(**settings).encode(obj)


_default_decoder = JSONDecoder()

def load(fp, cls=None, use_decimal=False, **kw):
    """Deserialize ``fp`` content to a Python object.

    :param fp: a ``.read()``-supporting file-like object containing
               a JSON document
    :keyword class cls: an alternative implementation of ``JSONDecoder``
    :keyword bool use_decimal: if ``True``, then it implies ``parse_float=decimal.Decimal``
                               for parity with ``dump``
    :rtype: object
    :return: a Python object equivalent to the content of the JSON stream

    To use a custom ``JSONDecoder`` subclass, specify it with the `cls` kwarg.

    .. note:: you should use `object_hook` or `object_pairs_hook` instead
              of subclassing whenever possible.

    Additional keyword arguments are forwarded to the :class:`JSONDecoder` constructor.
    """

    settings = {}
    settings.update(JSONDecoder.SENSIBLE_DEFAULTS)
    settings.update(kw)

    return loads(fp.read(), cls=cls, use_decimal=use_decimal, **settings)


def loads(s, cls=None, use_decimal=False, **kw):
    """Deserialize `s` to a Python object.

    :param str s: a string instance containing a JSON document
    :keyword class cls: an alternative implementation of ``JSONDecoder``
    :keyword bool use_decimal: if ``True``, then it implies ``parse_float=decimal.Decimal``
                               for parity with ``dump``
    :rtype: object
    :return: a Python object equivalent to the content of the JSON stream

    To use a custom ``JSONDecoder`` subclass, specify it with the `cls` kwarg.

    .. note:: you should use `object_hook` or `object_pairs_hook` instead
              of subclassing whenever possible.

    Additional keyword arguments are forwarded to the :class:`JSONDecoder` constructor.
    """

    settings = {}
    settings.update(JSONDecoder.SENSIBLE_DEFAULTS)
    settings.update(kw)

    if use_decimal:
        if settings['parse_float'] is not None:
            raise TypeError("use_decimal=True implies parse_float=Decimal")
        settings['parse_float'] = Decimal

    if (cls is None and settings == JSONDecoder.SENSIBLE_DEFAULTS):
        return _default_decoder.decode(s)

    if cls is None:
        cls = JSONDecoder

    return cls(**settings).decode(s)


def _toggle_speedups(enabled):
    from . import decoder as dec
    from . import encoder as enc
    from . import scanner as scan

    c_make_encoder = _import_c_make_encoder()
    if enabled:
        dec.scanstring = dec.c_scanstring or dec.py_scanstring
        enc.c_make_encoder = c_make_encoder
        enc.encode_basestring_ascii = (enc.c_encode_basestring_ascii or
            enc.py_encode_basestring_ascii)
        scan.make_scanner = scan.c_make_scanner or scan.py_make_scanner
    else:
        dec.scanstring = dec.py_scanstring
        enc.c_make_encoder = None
        enc.encode_basestring_ascii = enc.py_encode_basestring_ascii
        scan.make_scanner = scan.py_make_scanner
    dec.make_scanner = scan.make_scanner

    global _default_decoder
    _default_decoder = JSONDecoder(encoding=None,
                                   object_hook=None,
                                   object_pairs_hook=None)

    global _default_encoder
    _default_encoder = JSONEncoder(skipkeys=False,
                                   ensure_ascii=True,
                                   check_circular=True,
                                   allow_nan=True,
                                   indent=None,
                                   separators=None,
                                   encoding='utf-8',
                                   default=None)


def simple_first(kv):
    """Helper function to pass to item_sort_key to sort simple
    elements to the top, then container elements.
    """
    return (isinstance(kv[1], (list, dict, tuple)), kv[0])
