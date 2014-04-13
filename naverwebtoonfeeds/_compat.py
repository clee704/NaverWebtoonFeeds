"""
    naverwebtoonfeeds._compat
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Python 2/3 compatibility support. Original work by Armin Ronacher.

"""
import sys


PY2 = sys.version_info[0] == 2
_identity = lambda x: x


if not PY2:
    text_type = str
    string_types = (str,)
    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())

    from urllib.parse import urlparse, urlunparse

    def to_native(x, charset=sys.getdefaultencoding(), errors='strict'):
        if x is None or isinstance(x, str):
            return x
        return x.decode(charset, errors)

    implements_to_string = _identity

    from urllib.request import URLError, urlopen
else:
    text_type = unicode
    string_types = (str, unicode)
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()

    from urlparse import urlparse, urlunparse

    def to_native(x, charset=sys.getdefaultencoding(), errors='strict'):
        if x is None or isinstance(x, str):
            return x
        return x.encode(charset, errors)

    def implements_to_string(cls):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda x: x.__unicode__().encode('utf-8')
        return cls

    from urllib2 import URLError, urlopen
