#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
--------------------------------------------------------------------------------
    Author: Last_D
    Created Time: 2014-10-15 11:52:43 Wed
    Last Modified: 2014-10-31 20:23:21 Fri
    Description:
        http module can handle request info and set response info.
        `HttpError` object is used to raise HTTP errors.
        `RedirectError` is a subclass of `HttpError`.
        `Request` object is used to get some client request information from
         environment dictionary, such as submit form data, request method,
         request path info and some others.
        `Response` object is used to set some response information, such as
         response status and response headers including cookie.
    Change Activity:
        - Add HttpError and RedirectError.
        - Fix error: Forget to pass a `size` parameter to `read` method of
        file-like object, `environ['wsgi.input']`.
--------------------------------------------------------------------------------
"""

_version = 'LTok/0.2'

import cookie

from tools import to_str, to_unicode, Dict

import urlparse, re, urllib

# Response status
RESPONSE_STATUS = {
    # Informational
    100: 'Continue',
    101: 'Switch Protocols',
    102: 'Processing',

    # Successful
    200: 'OK',
    201: 'Created',
    202: 'Accept',
    203: 'Non Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi Status',
    226: 'IM Used',

    # Redirection
    300: 'Multiple Choice',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',

    # Client error
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Lenght Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request URI Too Large',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    418: 'I\'m a teapot',
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    426: 'Upgrade Required',
    428: 'Precondtion Required',
    429: 'Too Many Requests',
    431: 'Request Header Fields Too Large',
    449: 'Retry With',

    # Server error
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Geteway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    507: 'Insufficient Storage',
    510: 'Not Extended'
}

RE_RESPONSE_STATUS = re.compile(r'^\d\d\d(\ [\w\ ]+)?$')

RESPONSE_HEADERS = (
    'Accept-Ranges',
    'Age',
    'Allow',
    'Cache-Control',
    'Connection',
    'Content-Encoding',
    'Content-Language',
    'Content-Length',
    'Content-Location',
    'Content-MD5',
    'Content-Disposition',
    'Content-Range',
    'Content-Type',
    'Date',
    'Etag',
    'Expires',
    'Last-Modified',
    'Link',
    'Location',
    'P3P',
    'Pragma',
    'Proxy-Authenticate',
    'Refresh',
    'Retry-After',
    'Server',
    'Set-Cookie',
    'Strict-Transport-Security',
    'Trailer',
    'Transfer-Encoding',
    'Vary',
    'Via',
    'Warning',
    'WWW-Authenticate',
    'X-Frame-Options',
    'X-XSS-Protextion',
    'X-Content-Type-Options',
    'X-Forwarded-Proto',
    'X-Powered-By',
    'X-UA-Compatible'
)

RESPONSE_HEADER_DICT = dict(zip(map(lambda i: i.upper(), RESPONSE_HEADERS),\
        RESPONSE_HEADERS))
HEADER_X_POWERED_BY = ('X-Powered-By', _version)


class HttpError(Exception):
    """HTTP error"""
    def __init__(self, code):
        super(HttpError, self).__init__()
        self._status = '%s %s' % (code, RESPONSE_STATUS[code])

    @property
    def status(self):
        return self._status

    def __str__(self):
        return "HttpError: '%s'." % self.status

    __repr__ = __str__


class RedirectError(HttpError):
    """RedirectError"""
    def __init__(self, code, location):
        super(RedirectError, self).__init__(code)
        self._location = location

    @property
    def location(self):
        return self._location

    def __str__(self):
        return "RedirectError: '%s --> %s'." % (self.status, self.location)


def _convert(item):
    """Convert form data to unicode."""
    if isinstance(item, list):
        return [to_unicode(i) for i in item]
    if item.filename:
        return MultipartFile(item)
    return to_unicode(item)


class MultipartFile(object):
    """Multipart file storage get from request input."""
    def __init__(self, storage):
        self.filename = to_unicode(storage.filename)
        self.file = storage.file


class Request(object):
    """Request object for obtaining all http request information."""
    def __init__(self, environ):
        self._environ = environ

    def _data_from_post(self):
        """Get data from request method 'POST'"""
        body_size = self.content_length
        if body_size == 0:
            return None
        request_body = self._environ['wsgi.input'].read(body_size)
        body_dict = urlparse.parse_qs(request_body)
        data = dict()
        for key in body_dict:
            data[key] = _convert(body_dict[key])
        return data

    def _data_from_get(self):
        """Get data from request method 'GET'"""
        body_dict = urlparse.parse_qs(self._environ['QUERY_STRING'])
        data = dict()
        for key in body_dict:
            data[key] = _convert(body_dict[key])
        return data

    def data(self, **kwargs):
        """Get input data as dict containing values as unicode,
        list or MultipartFile. Parameters kwargs is default value.
        """
        if self.request_method == 'GET':
            data = self._data_from_get()
        if self.request_method == 'POST':
            data = self._data_from_post()
        if not kwargs:
            return Dict(**data)
        inputs = Dict()
        for k, v in kwargs.iteritems():
            inputs[k] = data.get(k, [v])[0]
        return inputs

    def get_argument(self, key, default=None):
        """Get value by name, return default value if key not found."""
        value = self.data().get(key, default)
        if isinstance(value, list):
            return value[0]
        return value

    def get_arguments(self, key):
        """Get multiple values by key."""
        value = self.data().get(key)
        if isinstance(value, list):
            return value[:]
        return [value]

    """
    The following methids to get some environ value as str.
    """

    @property
    def remote_addr(self):
        return self._environ.get('REMOTE_ADDR', '0.0.0.0')

    @property
    def content_length(self):
        return int(self._environ.get('CONTENT_LENGTH', 0))

    @property
    def document_root(self):
        return self._environ.get('DOCUMENT_ROOT', '')

    @property
    def query_string(self):
        return self._environ.get('QUERY_STRING', '')

    @property
    def request_method(self):
        return self._environ['REQUEST_METHOD']

    @property
    def path_info(self):
        """Get request path as str."""
        return urllib.unquote(self._environ.get('PATH_INFO', ''))

    @property
    def host(self):
        return self._environ.get('HTTP_HOST', '')

    @property
    def environ(self):
        return self._environ

    def _get_headers(self):
        hdrs = dict((k.upper(), to_unicode(v)) \
                for k, v in self._environ.iteritems() if k.startswith('HTTP_'))
        return hdrs

    @property
    def headers(self):
        """Get all HTTP headers with key as str and value as unicode."""
        return dict(**self._getheaders())

    def header(self, header, default=None):
        """Get header from request as unicode by header name,
        return default if not found.
        """
        return self._get_headers().get(header.upper(), default)

    def _get_cookies(self):
        cookie_str = self._environ.get('HTTP_COOKIE', None)
        if not cookie_str:
            return None
        cookie_dict = cookie.get_cookie(cookie_str)
        return cookie_dict

    @property
    def cookies(self):
        """Return all cookies as dict, name and value  is str."""
        try:
            return dict(**self._get_cookies())
        except:
            return None

    @property
    def url_params(self):
        """Get params(list), which is searched group from url regex."""
        if hasattr(self, '_url_params'):
            return self._url_params
        return None

    @url_params.setter
    def url_params(self, l_value):
        """Set url_params by list regex find from url."""
        self._url_params = l_value


class Response(object):
    """Response object."""
    def __init__(self):
        self._status = '200 OK'
        self._headers = {'Content-Type': 'text/html; charset=utf-8'}

    @property
    def headers(self):
        """Return response headers as list."""
        # convert header name to low case
        L = [(k, v) for k, v in self._headers.iteritems()]
        if hasattr(self, '_cookies'):
            for v in self._cookies.itervalues():
                L.append(('Set-Cookie', v))
        L.append(HEADER_X_POWERED_BY)
        return L

    def header(self, name):
        """Get header by name."""
        return self._headers.get(name)

    def set_header(self, name, value):
        """Set header by given name and value."""
        self._headers[name] = to_str(value)

    @property
    def content_type(self):
        """Get response Content-Type."""
        return self.header('Content-Type')

    @content_type.setter
    def content_type(self, value):
        """Set a respose Content-Type."""
        self.set_header('Content-Type', value)

    @property
    def content_length(self):
        """Get response Content-Length."""
        return self.header('Content-Length')

    @content_length.setter
    def content_length(self, value):
        """Set response Content-Length."""
        self.set_header('Content-Length', str(value))

    @property
    def location(self):
        """Get response redirect location."""
        return self.header('Location')

    @location.setter
    def location(self, value):
        """Set redirect location."""
        self.set_header('Location', value)

    def set_refresh(self, timeout, url):
        self.set_header('Refresh', '%d; url=%s' % (timeout, url))

    def set_cookie(self, name, value, max_age=None, expires=None, path='/',\
            domain=None, secure=False, http_only=True):
        """Set a cookie with set_cookie function from cookie module."""
        cookies = cookie.set_cookie(name, value, max_age, expires, path, domain, \
                secure, http_only)

        if not hasattr(self, '_cookies'):
            self._cookies = {}
        self._cookies[name] = cookies
        self.set_header('Set-Cookie', cookies)

    def del_cookie(self, name):
        """Delete a cookie immediately."""
        cookie.del_cookie(name)

    @property
    def status(self):
        """Return response status."""
        return self._status

    @status.setter
    def status(self, value):
        """Set status by str or number."""
        if isinstance(value, (int, long)):
            if 100 <= value <= 999:
                status = RESPONSE_STATUS.get(value, '')
                if status:
                    self._status = status
                else:
                    self._status = str(value)
            else:
                raise ValueError('Bad response status: %d.' % value)
        elif isinstance(value, basestring):
            value = to_str(value)
            if RE_RESPONSE_STATUS.match(value):
                self._status = value
            else:
                raise ValueError('Bad response status %s.' % value)
        else:
            raise TypeError('Bad type of response status.')


