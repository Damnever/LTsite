#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
--------------------------------------------------------------------------------
    Author: Last_D
    Created Time: 2014-10-13 11:04:52 Mon
    Last Modified: 2014-10-25 15:23:25 Sat
    Description:
        Some Tools for web framwork.
        A dict object but support access as x.y style.
        A UTC tzinfo object.
    Change Activity:
        - Add doc test.
--------------------------------------------------------------------------------
"""

import re
import datetime
import urllib

def to_str(s):
    """Convert to str"""
    if isinstance(s, unicode):
        return s.encode('utf-8')
    return str(s)

def to_unicode(s, encoding='utf-8'):
    """Convert str to unicode"""
    return s.decode(encoding)

def quote(s, encoding='utf-8'):
    """Url quote as str."""
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return urllib.quote(s)

def unquote(s, encoding='utf-8'):
    """Url unquote as unicode."""
    return urllib.unquote(s).decode('utf-8')

class Dict(dict):
    """
    Simple dict but support access as x.y style.

    >>> d1 = Dict(x=100, y='200')
    >>> d1['x']
    100
    >>> d1.y
    '200'
    >>> d1['empty']
    Traceback (most recent call last):
        ...
    KeyError: 'empty'
    >>> d1.empty
    Traceback (most recent call last):
        ...
    AttributeError: 'Dict' object has no attribute 'empty'
    """
    def __init__(self, names=(), values=(), **kwargs):
        super(Dict, self).__init__(**kwargs)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError("'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


_TIMEDELTA_ZERO = datetime.timedelta(0)

_RE_TZ = re.compile('^([\+\-])([0-9]{1,2})\:([0-9]{1,2})$')  # such as +8:00

class UTC(datetime.tzinfo):
    """
    A UTC class inherited from the tzinfo which has no DST.

    >>> tz0 = UTC('+00:00')
    >>> tz0.tzname(None)
    'UTC+00:00'
    >>> tz8 = UTC('+8:00')
    >>> tz8.tzname(None)
    'UTC+8:00'
    >>> from datetime import datetime
    >>> u = datetime.utcnow().replace(tzinfo=tz0)
    >>> l1 = u.astimezone(tz8)
    >>> l2 = u.replace(tzinfo=tz8)
    >>> d1 = u - l1
    >>> d2 = u - l2
    >>> d1.seconds
    0
    >>> d2.seconds
    28800
    """
    def __init__(self, utc):
        utc = str(utc.strip().upper())
        mt = _RE_TZ.match(utc)
        if mt:
            minus = mt.group(1)=='-'
            h = int(mt.group(2))
            m = int(mt.group(3))
            if minus:
                h, m = (-h), (-m)
            self._utcoffset = datetime.timedelta(hours=h, minutes=m)
            self._tzname = 'UTC%s' % utc
        else:
            raise ValueError('bad utc time zone')

    def utcoffset(self, dt):
        """no DST"""
        return self._utcoffset

    def dst(self, dt):
        return _TIMEDELTA_ZERO

    def tzname(self, dt):
        return self._tzname

    def __str__(self):
        return 'UTC tzinfo object (%s)' % self._tzname

    __repr__ = __str__


if __name__ == '__main__':
    import doctest
    doctest.testmod()
