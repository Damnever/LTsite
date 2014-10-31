#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
--------------------------------------------------------------------------------
    Author: Last_D
    Created Time: 2014-10-15 12:31:18 Wed
    Last Modified: 2014-10-22 22:46:30 Wed
    Description:
        Cookie module which can set cookie as str and load cookie string as
        dict, delete cookie immediately.
    Change Activity:
        - Add doctest.
        - None
--------------------------------------------------------------------------------
"""

from tools import UTC

import Cookie, datetime, shelve, time, os, sha, urllib

# GMT
UTC_0 = UTC('+00:00')

def set_cookie(name, value, max_age=(7*24*60*60), expires=None, path='/',\
        domain=None, secure=False, http_only=True):
    """
    Set a cookie with Cookie.SimpleCookie class.
    Refer to RFC 2109.

    Parameters:
        name: the cookie name.
        value: the cookie value.
        max_age: optional, the Max-Age attribute defines the lifetime of the
            cookie, in seconds the delta-seconds value is a decimal non-negative
            integer. Default value is one week.
        expires: optional, unix timestamp, datetime or date object that indicate
            an absolute time of the expiration of cookie. Note that if expires
            specified, the Max-Age will be ignore.
        path: optional, the Path attribute specifies the subset of URLs to which
            this cookie applies. Default to '/'.
        domain: optional, the Domain attribute specifies the domain for which the
            cookie is valid. An explicity specified domain must always start with
            a dot. Default to None.
        secure: set the cookie secure, default to False.
        http_only: set cookie for http only, default to True for better safty.
    """
    cookie = Cookie.SimpleCookie()
    cookie[name] = value
    if expires is not None:
        if isinstance(expires, (int, float, long)):
            cookie[name]['expires'] = datetime.datetime.fromtimestamp(expires,\
                    UTC_0).strftime('%a, %d %b %Y %H:%M:%S GMT')
        if isinstance(expires, (datetime.date, datetime.datetime)):
            cookie[name]['expires'] = expires.astimezone(UTC_0).strftime('%a, \
                    %d %b %Y %H:%M:%S GMT')
    elif isinstance(max_age, (int, long)):
        cookie[name]['max-age'] = max_age
    cookie[name]['path'] = path
    if domain:
        cookie[name]['domain'] = domain
    if secure:
        cookie[name]['secure'] = secure
    if http_only:
        cookie[name]['httponly'] = http_only
    return cookie.output(header='').strip()

def get_cookie(s):
    """Load cookie from str as dict. the name and value both are str."""
    cookies = {}
    for each in s.split(';'):
        pos = each.find('=')
        if pos > 0:
            cookies[each[:pos].strip()] = urllib.unquote(each[pos+1:])
    return cookies

def del_cookie(name):
    """Delete a cookie by the cookie name."""
    set_cookie(name, '__deleted__', expires=0)

# session  #####**unused**#####
SESSION_DIR = './session'

def set_session(name, value, expires=(12*60*60), cookie_path='/'):
    """Set a session, first set a cookie, then it is stroed in server side,
    default to './tmp'
    """
    cookie = Cookie.SimpleCookie()
    sid = sha.new(repr(time.time())).hexdigest()
    cookie[name] = sid
    cookie[name]['path'] = cookie_path
    cookie[name]['expires'] = expires
    if not os.path.exists(SESSION_DIR):
        try:
            os.mkdir(SESSION_DIR, 02770)
        except OSError as e:
            errmsg = "%s when trying to create the directory. Create \
                    it as '%s'" % (e.strerror, os.path.abspath(SESSION_DIR))
            raise OSError(errmsg)
    data = shelve.open(SESSION_DIR + '/sess_' + sid, writeback=True)
    os.chmod(SESSION_DIR + '/sess_' + sid, 0660)
    session = dict()
    session['value'] = value
    session['expires'] = expires
    data['session'] = session
    data.close()
    return cookie.output(header='').strip()

def get_session(name, sid):
    """Get a session by cookie name, depend on the sid of cookie open file,
    then can get the value.
    """
    if not os.path.exists(SESSION_DIR + '/sess_' + sid):
        return None
    data = shelve.open(SESSION_DIR + '/sess_' + sid)
    if 'session' not in data:
        os.remove(SESSION_DIR + 'sess_' + sid)
        return None
    return data['session']['value']
