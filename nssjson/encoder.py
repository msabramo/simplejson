"""Implementation of JSONEncoder
"""
from __future__ import absolute_import
import re
from operator import itemgetter
from datetime import date, datetime, time
from decimal import Decimal
from .compat import u, unichr, binary_type, string_types, integer_types, PY3, utc
def _import_speedups():
    try:
        from . import _speedups
        return _speedups.encode_basestring_ascii, _speedups.make_encoder
    except ImportError:
        return None, None
c_encode_basestring_ascii, c_make_encoder = _import_speedups()

from nssjson.decoder import PosInf

#ESCAPE = re.compile(ur'[\x00-\x1f\\"\b\f\n\r\t\u2028\u2029]')
# This is required because u() will mangle the string and ur'' isn't valid
# python3 syntax
ESCAPE = re.compile(u'[\\x00-\\x1f\\\\"\\b\\f\\n\\r\\t\u2028\u2029]')
ESCAPE_ASCII = re.compile(r'([\\"]|[^\ -~])')
HAS_UTF8 = re.compile(r'[\x80-\xff]')
ESCAPE_DCT = {
    '\\': '\\\\',
    '"': '\\"',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
}
for i in range(0x20):
    #ESCAPE_DCT.setdefault(chr(i), '\\u{0:04x}'.format(i))
    ESCAPE_DCT.setdefault(chr(i), '\\u%04x' % (i,))
for i in [0x2028, 0x2029]:
    ESCAPE_DCT.setdefault(unichr(i), '\\u%04x' % (i,))

FLOAT_REPR = repr

def encode_basestring(s, _PY3=PY3, _q=u('"')):
    """Return a JSON representation of a Python string

    """
    if _PY3:
        if isinstance(s, binary_type):
            s = s.decode('utf-8')
    else:
        if isinstance(s, str) and HAS_UTF8.search(s) is not None:
            s = s.decode('utf-8')
    def replace(match):
        return ESCAPE_DCT[match.group(0)]
    return _q + ESCAPE.sub(replace, s) + _q


def py_encode_basestring_ascii(s, _PY3=PY3):
    """Return an ASCII-only JSON representation of a Python string

    """
    if _PY3:
        if isinstance(s, binary_type):
            s = s.decode('utf-8')
    else:
        if isinstance(s, str) and HAS_UTF8.search(s) is not None:
            s = s.decode('utf-8')
    def replace(match):
        s = match.group(0)
        try:
            return ESCAPE_DCT[s]
        except KeyError:
            n = ord(s)
            if n < 0x10000:
                #return '\\u{0:04x}'.format(n)
                return '\\u%04x' % (n,)
            else:
                # surrogate pair
                n -= 0x10000
                s1 = 0xd800 | ((n >> 10) & 0x3ff)
                s2 = 0xdc00 | (n & 0x3ff)
                #return '\\u{0:04x}\\u{1:04x}'.format(s1, s2)
                return '\\u%04x\\u%04x' % (s1, s2)
    return '"' + str(ESCAPE_ASCII.sub(replace, s)) + '"'


encode_basestring_ascii = (
    c_encode_basestring_ascii or py_encode_basestring_ascii)


class JSONEncoder(object):
    """Extensible JSON <http://json.org> encoder for Python data structures.

    Supports the following objects and types by default:

    +-------------------+---------------+
    | Python            | JSON          |
    +===================+===============+
    | dict, namedtuple  | object        |
    +-------------------+---------------+
    | list, tuple       | array         |
    +-------------------+---------------+
    | str, unicode      | string        |
    +-------------------+---------------+
    | int, long, float  | number        |
    +-------------------+---------------+
    | True              | true          |
    +-------------------+---------------+
    | False             | false         |
    +-------------------+---------------+
    | None              | null          |
    +-------------------+---------------+

    To extend this to recognize other objects, subclass and implement a
    ``.default()`` method with another method that returns a serializable
    object for ``o`` if possible, otherwise it should call the superclass
    implementation (to raise ``TypeError``).
    """

    SENSIBLE_DEFAULTS = {
        'allow_nan': True,
        'bigint_as_string': False,
        'check_circular': True,
        'default': None,
        'encoding': 'utf-8',
        'ensure_ascii': True,
        'for_json': False,
        'ignore_nan': False,
        'indent': None,
        'iso_datetime': False,
        'item_sort_key': None,
        'namedtuple_as_object': True,
        'separators': None,
        'skipkeys': False,
        'sort_keys': False,
        'tuple_as_array': True,
        'use_decimal': True,
        'utc_datetime': False,
    }

    item_separator = ', '
    key_separator = ': '
    def __init__(self, **kw):
        """Constructor for JSONEncoder.

        :keyword bool allow_nan: if ``False``, then it will be a ``ValueError`` to serialize
          out of range ``float`` values (``nan``, ``inf``, ``-inf``) in strict compliance of
          the JSON specification, instead of using the JavaScript equivalents (``NaN``,
          ``Infinity``, ``-Infinity``) [default: ``True``]

        :keyword bool bigint_as_string: if ``True``, then ints 2**53 and higher or lower than
          -2**53 will be encoded as strings. This is to avoid the rounding that happens in
          Javascript otherwise. Note that this is still a lossy operation that will not
          round-trip correctly and should be used sparingly [default: ``False``]

        :keyword bool check_circular: if ``False``, then the circular reference check for
          container types will be skipped and a circular reference will result in an
          ``OverflowError`` (or worse) [default: ``True``]

        :keyword callable default: a function that gets called for objects that can't otherwise
          be serialized and should return a serializable version of `obj` or raise
          ``TypeError``; if ``None`` a ``TypeError`` is generated in such cases [default:
          ``None``]

        :keyword str encoding: the character encoding for ``str`` instances [default:
          ``'utf-8'``]

        :keyword bool ensure_ascii: if ``True``, then the output is guaranteed to be str
          objects with all incoming unicode characters escaped, otherwise it will be unicode
          object [default: ``True``]

        :keyword bool for_json: if ``True``, then objects with a ``for_json()`` method will use
          the return value of that method for encoding as JSON instead of the object [default:
          ``False``]

        :keyword bool ignore_nan: if ``True``, then out of range :class:`float` values
          (``nan``, ``inf``, ``-inf``) will be serialized as ``null`` in compliance with the
          ECMA-262 specification, overriding `allow_nan` [default: ``False``]

        :keyword str indent: if given, then JSON array elements and object members will be
          pretty-printed with a newline followed by that string repeated for each level of
          nesting; a ``None`` value selects the most compact representation without any
          newlines; an integer is also accepted and is converted to a string with that many
          spaces [default: ``None``]

        :keyword bool iso_datetime: if ``True``, then ``datetime.datetime``, ``datetime.date``
          and ``datetime.time`` will be directly supported; otherwise they will raise a
          ``ValueError`` (if not handled by the `default` function) [default: ``False``]

        :keyword callable item_sort_key: used to sort the items in each dictionary, useful if
          you want to sort items other than in alphabetical order by key; this option takes
          precedence over `sort_keys` [default: ``None``]

        :keyword bool namedtuple_as_object: if ``True``, then tuple subclasses with
          ``_asdict()`` methods will be encoded as JSON objects [default: ``True``]

        :keyword tuple separators: if given, it should be an ``(item_separator,
          key_separator)`` tuple; to get the most compact JSON representation, you should
          specify ``(',', ':')`` to eliminate whitespace [default: ``(', ', ': ')`` if `indent`
          is ``None`` and ``(',', ': ')`` otherwise]

        :keyword bool skipkeys: if ``True``, then ``dict`` keys that are not basic types
          (``str``, ``unicode``, ``int``, ``long``, ``float``, ``bool``, ``None``) will be
          skipped instead of raising a ``TypeError`` [default: ``False``]

        :keyword bool sort_keys: if ``True``, then the output of dictionaries will be sorted by
          item [default: ``False``]

        :keyword bool tuple_as_array: if ``True``, then tuples (and subclasses) will be encoded
          as JSON arrays [default: ``True``]

        :keyword bool use_decimal: if ``True``, then :class:`decimal.Decimal` will be natively
          serialized to JSON with full precision [default: ``True``]

        :keyword bool utc_datetime: if ``True``, then timezone aware datetimes are converted to
          UTC upon serialization [default: ``False``]
        """

        defaults = self.SENSIBLE_DEFAULTS

        skipkeys = kw.get('skipkeys', defaults['skipkeys'])
        self.skipkeys = skipkeys
        ensure_ascii = kw.get('ensure_ascii', defaults['ensure_ascii'])
        self.ensure_ascii = ensure_ascii
        check_circular = kw.get('check_circular', defaults['check_circular'])
        self.check_circular = check_circular
        allow_nan = kw.get('allow_nan', defaults['allow_nan'])
        self.allow_nan = allow_nan
        sort_keys = kw.get('sort_keys', defaults['sort_keys'])
        self.sort_keys = sort_keys
        use_decimal = kw.get('use_decimal', defaults['use_decimal'])
        self.use_decimal = use_decimal
        iso_datetime = kw.get('iso_datetime', defaults['iso_datetime'])
        self.iso_datetime = iso_datetime
        utc_datetime = kw.get('utc_datetime', defaults['utc_datetime'])
        self.utc_datetime = utc_datetime
        namedtuple_as_object = kw.get('namedtuple_as_object', defaults['namedtuple_as_object'])
        self.namedtuple_as_object = namedtuple_as_object
        tuple_as_array = kw.get('tuple_as_array', defaults['tuple_as_array'])
        self.tuple_as_array = tuple_as_array
        bigint_as_string = kw.get('bigint_as_string', defaults['bigint_as_string'])
        self.bigint_as_string = bigint_as_string
        item_sort_key = kw.get('item_sort_key', defaults['item_sort_key'])
        self.item_sort_key = item_sort_key
        for_json = kw.get('for_json', defaults['for_json'])
        self.for_json = for_json
        ignore_nan = kw.get('ignore_nan', defaults['ignore_nan'])
        self.ignore_nan = ignore_nan
        indent = kw.get('indent', defaults['indent'])
        if indent is not None and not isinstance(indent, string_types):
            indent = indent * ' '
        self.indent = indent
        separators = kw.get('separators', defaults['separators'])
        if separators is not None:
            self.item_separator, self.key_separator = separators
        elif indent is not None:
            self.item_separator = ','
        default = kw.get('default', defaults['default'])
        if default is not None:
            self.default = default
        encoding = kw.get('encoding', defaults['encoding'])
        self.encoding = encoding

    def default(self, o):
        """Implement this method in a subclass such that it returns
        a serializable object for ``o``, or calls the base implementation
        (to raise a ``TypeError``).

        For example, to support arbitrary iterators, you could
        implement default like this::

            def default(self, o):
                try:
                    iterable = iter(o)
                except TypeError:
                    pass
                else:
                    return list(iterable)
                return JSONEncoder.default(self, o)

        """
        raise TypeError(repr(o) + " is not JSON serializable")

    def encode(self, o):
        """Return a JSON string representation of a Python data structure.

        >>> from nssjson import JSONEncoder
        >>> JSONEncoder().encode({"foo": ["bar", "baz"]})
        '{"foo": ["bar", "baz"]}'

        """
        # This is for extremely simple cases and benchmarks.
        if isinstance(o, binary_type):
            _encoding = self.encoding
            if (_encoding is not None and not (_encoding == 'utf-8')):
                o = o.decode(_encoding)
        if isinstance(o, string_types):
            if self.ensure_ascii:
                return encode_basestring_ascii(o)
            else:
                return encode_basestring(o)
        # This doesn't pass the iterator directly to ''.join() because the
        # exceptions aren't as detailed.  The list call should be roughly
        # equivalent to the PySequence_Fast that ''.join() would do.
        chunks = self.iterencode(o)
        if not isinstance(chunks, (list, tuple)):
            chunks = list(chunks)
        if self.ensure_ascii:
            return ''.join(chunks)
        else:
            return u''.join(chunks)

    def iterencode(self, o):
        """Encode the given object and yield each string
        representation as available.

        For example::

            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)

        """
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = encode_basestring_ascii
        else:
            _encoder = encode_basestring
        if self.encoding != 'utf-8':
            def _encoder(o, _orig_encoder=_encoder, _encoding=self.encoding):
                if isinstance(o, binary_type):
                    o = o.decode(_encoding)
                return _orig_encoder(o)

        def floatstr(o, allow_nan=self.allow_nan, ignore_nan=self.ignore_nan,
                _repr=FLOAT_REPR, _inf=PosInf, _neginf=-PosInf):
            # Check for specials. Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on
            # the internals.

            if o != o:
                text = 'NaN'
            elif o == _inf:
                text = 'Infinity'
            elif o == _neginf:
                text = '-Infinity'
            else:
                return _repr(o)

            if ignore_nan:
                text = 'null'
            elif not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text

        key_memo = {}
        if c_make_encoder is not None and self.indent is None:
            _iterencode = c_make_encoder(
                markers, self.default, _encoder, self.indent,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys, self.allow_nan, key_memo,
                self.use_decimal, self.iso_datetime, self.utc_datetime,
                self.namedtuple_as_object, self.tuple_as_array,
                self.bigint_as_string, self.item_sort_key,
                self.encoding, self.for_json, self.ignore_nan,
                Decimal)
        else:
            _iterencode = _make_iterencode(
                markers, self.default, _encoder, self.indent, floatstr,
                self.key_separator, self.item_separator, self.sort_keys,
                self.skipkeys,
                self.use_decimal, self.iso_datetime, self.utc_datetime,
                self.namedtuple_as_object, self.tuple_as_array,
                self.bigint_as_string, self.item_sort_key,
                self.encoding, self.for_json,
                Decimal=Decimal)
        try:
            return _iterencode(o, 0)
        finally:
            key_memo.clear()


class JSONEncoderForHTML(JSONEncoder):
    """An encoder that produces JSON safe to embed in HTML.

    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.
    """

    def encode(self, o):
        # Override JSONEncoder.encode because it has hacks for
        # performance that make things more complicated.
        chunks = self.iterencode(o)
        if self.ensure_ascii:
            return ''.join(chunks)
        else:
            return u''.join(chunks)

    def iterencode(self, o):
        chunks = super(JSONEncoderForHTML, self).iterencode(o)
        for chunk in chunks:
            chunk = chunk.replace('&', '\\u0026')
            chunk = chunk.replace('<', '\\u003c')
            chunk = chunk.replace('>', '\\u003e')
            yield chunk


def _make_iterencode(
        markers, _default, _encoder, _indent, _floatstr, _key_separator,
        _item_separator, _sort_keys, _skipkeys, _use_decimal,
        _iso_datetime, _utc_datetime, _namedtuple_as_object, _tuple_as_array,
        _bigint_as_string, _item_sort_key, _encoding, _for_json,
        ## HACK: hand-optimized bytecode; turn globals into locals
        _PY3=PY3,
        ValueError=ValueError,
        string_types=string_types,
        Decimal=Decimal,
        dict=dict,
        float=float,
        id=id,
        integer_types=integer_types,
        isinstance=isinstance,
        list=list,
        str=str,
        tuple=tuple,
        datetime=datetime,
        date=date,
        time=time,
        utc=utc,
    ):
    if _item_sort_key and not callable(_item_sort_key):
        raise TypeError("item_sort_key must be None or callable")
    elif _sort_keys and not _item_sort_key:
        _item_sort_key = itemgetter(0)

    def _iterencode_list(lst, _current_indent_level):
        if not lst:
            yield '[]'
            return
        if markers is not None:
            markerid = id(lst)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = lst
        buf = '['
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + (_indent * _current_indent_level)
            separator = _item_separator + newline_indent
            buf += newline_indent
        else:
            newline_indent = None
            separator = _item_separator
        first = True
        for value in lst:
            if first:
                first = False
            else:
                buf = separator
            if (isinstance(value, string_types) or
                (_PY3 and isinstance(value, binary_type))):
                yield buf + _encoder(value)
            elif value is None:
                yield buf + 'null'
            elif value is True:
                yield buf + 'true'
            elif value is False:
                yield buf + 'false'
            elif isinstance(value, integer_types):
                yield ((buf + str(value))
                       if (not _bigint_as_string or
                           (-1 << 53) < value < (1 << 53))
                           else (buf + '"' + str(value) + '"'))
            elif isinstance(value, float):
                yield buf + _floatstr(value)
            elif _use_decimal and isinstance(value, Decimal):
                yield buf + str(value)
            elif _iso_datetime and isinstance(value, datetime):
                utcoffset = value.utcoffset()
                isutc = utcoffset is not None and not(utcoffset)
                if _utc_datetime or isutc:
                    if utcoffset is not None and not isutc:
                        value = value.astimezone(utc)
                    yield buf + '"%sZ"' % value.isoformat().split('+')[0]
                else:
                    yield buf + '"%s"' % value.isoformat().split('+')[0]
            elif _iso_datetime and isinstance(value, (date, time)):
                yield buf + '"%s"' % value.isoformat()
            else:
                yield buf
                for_json = _for_json and getattr(value, 'for_json', None)
                if for_json and callable(for_json):
                    chunks = _iterencode(for_json(), _current_indent_level)
                elif isinstance(value, list):
                    chunks = _iterencode_list(value, _current_indent_level)
                else:
                    _asdict = _namedtuple_as_object and getattr(value, '_asdict', None)
                    if _asdict and callable(_asdict):
                        chunks = _iterencode_dict(_asdict(),
                                                  _current_indent_level)
                    elif _tuple_as_array and isinstance(value, tuple):
                        chunks = _iterencode_list(value, _current_indent_level)
                    elif isinstance(value, dict):
                        chunks = _iterencode_dict(value, _current_indent_level)
                    else:
                        chunks = _iterencode(value, _current_indent_level)
                for chunk in chunks:
                    yield chunk
        if newline_indent is not None:
            _current_indent_level -= 1
            yield '\n' + (_indent * _current_indent_level)
        yield ']'
        if markers is not None:
            del markers[markerid]

    def _stringify_key(key):
        if isinstance(key, string_types): # pragma: no cover
            pass
        elif isinstance(key, binary_type):
            key = key.decode(_encoding)
        elif isinstance(key, float):
            key = _floatstr(key)
        elif key is True:
            key = 'true'
        elif key is False:
            key = 'false'
        elif key is None:
            key = 'null'
        elif isinstance(key, integer_types):
            key = str(key)
        elif _use_decimal and isinstance(key, Decimal):
            key = str(key)
        elif _iso_datetime and isinstance(key, datetime):
            utcoffset = key.utcoffset()
            isutc = utcoffset is not None and not(utcoffset)
            if _utc_datetime or isutc:
                if utcoffset is not None and not isutc:
                    key = key.astimezone(utc)
                key = '%sZ' % key.isoformat().split('+')[0]
            else:
                key = '%s' % key.isoformat().split('+')[0]
        elif _iso_datetime and isinstance(key, (date, time)):
            key = key.isoformat()
        elif _skipkeys:
            key = None
        else:
            raise TypeError("key " + repr(key) + " is not a string")
        return key

    def _iterencode_dict(dct, _current_indent_level):
        if not dct:
            yield '{}'
            return
        if markers is not None:
            markerid = id(dct)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = dct
        yield '{'
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + (_indent * _current_indent_level)
            item_separator = _item_separator + newline_indent
            yield newline_indent
        else:
            newline_indent = None
            item_separator = _item_separator
        first = True
        if _PY3:
            iteritems = dct.items()
        else:
            iteritems = dct.iteritems()
        if _item_sort_key:
            items = []
            for k, v in dct.items():
                if not isinstance(k, string_types):
                    k = _stringify_key(k)
                    if k is None:
                        continue
                items.append((k, v))
            items.sort(key=_item_sort_key)
        else:
            items = iteritems
        for key, value in items:
            if not (_item_sort_key or isinstance(key, string_types)):
                key = _stringify_key(key)
                if key is None:
                    # _skipkeys must be True
                    continue
            if first:
                first = False
            else:
                yield item_separator
            yield _encoder(key)
            yield _key_separator
            if (isinstance(value, string_types) or
                (_PY3 and isinstance(value, binary_type))):
                yield _encoder(value)
            elif value is None:
                yield 'null'
            elif value is True:
                yield 'true'
            elif value is False:
                yield 'false'
            elif isinstance(value, integer_types):
                yield (str(value)
                       if (not _bigint_as_string or
                           (-1 << 53) < value < (1 << 53))
                           else ('"' + str(value) + '"'))
            elif isinstance(value, float):
                yield _floatstr(value)
            elif _use_decimal and isinstance(value, Decimal):
                yield str(value)
            elif _iso_datetime and isinstance(value, datetime):
                utcoffset = value.utcoffset()
                isutc = utcoffset is not None and not(utcoffset)
                if _utc_datetime or isutc:
                    if utcoffset is not None and not isutc:
                        value = value.astimezone(utc)
                    yield '"%sZ"' % value.isoformat().split('+')[0]
                else:
                    yield '"%s"' % value.isoformat().split('+')[0]
            elif _iso_datetime and isinstance(value, (date, time)):
                yield '"%s"' % value.isoformat()
            else:
                for_json = _for_json and getattr(value, 'for_json', None)
                if for_json and callable(for_json):
                    chunks = _iterencode(for_json(), _current_indent_level)
                elif isinstance(value, list):
                    chunks = _iterencode_list(value, _current_indent_level)
                else:
                    _asdict = _namedtuple_as_object and getattr(value, '_asdict', None)
                    if _asdict and callable(_asdict):
                        chunks = _iterencode_dict(_asdict(),
                                                  _current_indent_level)
                    elif _tuple_as_array and isinstance(value, tuple):
                        chunks = _iterencode_list(value, _current_indent_level)
                    elif isinstance(value, dict):
                        chunks = _iterencode_dict(value, _current_indent_level)
                    else:
                        chunks = _iterencode(value, _current_indent_level)
                for chunk in chunks:
                    yield chunk
        if newline_indent is not None:
            _current_indent_level -= 1
            yield '\n' + (_indent * _current_indent_level)
        yield '}'
        if markers is not None:
            del markers[markerid]

    def _iterencode(o, _current_indent_level):
        if (isinstance(o, string_types) or
            (_PY3 and isinstance(o, binary_type))):
            yield _encoder(o)
        elif o is None:
            yield 'null'
        elif o is True:
            yield 'true'
        elif o is False:
            yield 'false'
        elif isinstance(o, integer_types):
            yield (str(o)
                   if (not _bigint_as_string or
                       (-1 << 53) < o < (1 << 53))
                       else ('"' + str(o) + '"'))
        elif isinstance(o, float):
            yield _floatstr(o)
        else:
            for_json = _for_json and getattr(o, 'for_json', None)
            if for_json and callable(for_json):
                for chunk in _iterencode(for_json(), _current_indent_level):
                    yield chunk
            elif isinstance(o, list):
                for chunk in _iterencode_list(o, _current_indent_level):
                    yield chunk
            else:
                _asdict = _namedtuple_as_object and getattr(o, '_asdict', None)
                if _asdict and callable(_asdict):
                    for chunk in _iterencode_dict(_asdict(),
                            _current_indent_level):
                        yield chunk
                elif (_tuple_as_array and isinstance(o, tuple)):
                    for chunk in _iterencode_list(o, _current_indent_level):
                        yield chunk
                elif isinstance(o, dict):
                    for chunk in _iterencode_dict(o, _current_indent_level):
                        yield chunk
                elif _use_decimal and isinstance(o, Decimal):
                    yield str(o)
                elif _iso_datetime and isinstance(o, datetime):
                    utcoffset = o.utcoffset()
                    isutc = utcoffset is not None and not(utcoffset)
                    if _utc_datetime or isutc:
                        if utcoffset is not None and not isutc:
                            o = o.astimezone(utc)
                        yield '"%sZ"' % o.isoformat().split('+')[0]
                    else:
                        yield '"%s"' % o.isoformat().split('+')[0]
                elif _iso_datetime and isinstance(o, (date, time)):
                    yield '"%s"' % o.isoformat()
                else:
                    if markers is not None:
                        markerid = id(o)
                        if markerid in markers:
                            raise ValueError("Circular reference detected")
                        markers[markerid] = o
                    o = _default(o)
                    for chunk in _iterencode(o, _current_indent_level):
                        yield chunk
                    if markers is not None:
                        del markers[markerid]

    return _iterencode
