#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
================================================================================
    Author: Last_D
    Created Time: 2014-10-13 20:34:41 Mon
    Last Modified: 2014-10-15 12:19:03 Wed
    Description:
        A light-weight WSGI web framework, let's wait and see!
    Change Activity:
        - Refer to: https://github.com/michaelliao/awesome-python-webapp/blob/
                    release/www/transwarp/web.py
        - Add response status, reponse headers and Request class.
        - Add Reponse class.
        - Add @get/@post decorator which is used to mapping URL route.
        - Add template engine default to Jinja2, and implement WSGI application.
          Then testing my web framwork, access to the page will work, but found
          a error:
              AttributeError: 'NoneType' object has no attribute 'split'.
        - none
================================================================================
"""

__version__ = 'LTok/0.1'

from tools import Dict, UTC

import os.path, re, logging, threading, urllib, Cookie, mimetypes, datetime
import types, urlparse

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

# thread local object for store request and response
ctx = threading.local()

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
HEADER_X_POWERED_BY = ('X-Powered-By', __version__)


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


class MultipartFile(object):
    """Multipart file storage get from request input."""
    def __init__(self, storage):
        self.filename = to_unicode(storage.filename)
        self.file = storage.file

class Request(object):
    """Request object for obtaining all http request information."""
    def __init__(self, environ):
        self._environ = environ

    def _parse_input(self):
        def _convert(item):
            if isinstance(item, list):
                return [to_unicode(i) for i in item]
            if item.filename:
                return MultipartFile(item)
            return to_unicode(item)
        request_body_size = self.content_length
        request_body = self._environ['wsgi.input'].read(request_body_size)
        body_dict = urlparse.parse_qs(request_body)
        inputs = dict()
        for key in body_dict:
            inputs[key] = _convert(body_dict[key])
        return inputs

    def _get_raw_input(self):
        """
        Get raw input as dict containing values as unicode,
        list or MultipartFile.
        """
        if not hasattr(self, '_raw_input'):
            self._raw_input = self._parse_input()
        return self._raw_input

    def get(self, key, default=None):
        """Get value by name, return default value if key not found."""
        value = self._get_raw_input().get(key, default)
        if isinstance(value, list):
            return value[0]
        return value

    def getlist(self, key):
        """Get multiple values by key."""
        value = self._get_raw_input()[key]
        if isinstance(value, list):
            return value[:]
        return [value]

    def input(self, **kw):
        """Get input value, return given default kwargs if key not found."""
        copy = Dict(**kw)
        raw = self._get_raw_input()
        for k, v in raw.iteritems():
            copy[k] = v[0] if isinstance(v, list) else v
        return copy

    # Get some environ value.
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
        cookie_str = self._environ.get('HTTP_COOKIE')
        cookie_obj = Cookie.SimpleCookie.load(cookie_str)
        # convert cookie object as dict
        cookies = dict((k, unquote(cookie_obj[k].value)) for k in cookie_obj)
        cookies.update(dict((k, unquote(cookie_obj[k][k2])) for k in cookies \
                for k2 in cookie_obj if cookie_obj[k][k2] != ''))
        return cookies

    @property
    def cookies(self):
        """Return all cookies as dict, name is str and value is unicode."""
        return dict(**self._get_cookies())

    def cookie(self, name, default=None):
        """Return cookie by name as unicode."""
        return self._get_cookies().get(name, default)

# GMT
UTC_0 = UTC('+00:00')

class Response(object):
    """Response object."""
    def __init__(self):
        self._status = '200 OK'
        self._headers = {'CONTENT_TYPE': 'text/html; charset=utf-8'}

    @property
    def headers(self):
        """Return response headers as list."""
        # convert header name to low case
        L = [(RESPONSE_HEADER_DICT.get(k, k), v) \
                for k, v in self._headers.iteritems()]
        if hasattr(self, '_cookies'):
            for v in self._cookies.itervalues():
                L.append(('Set-Cookie', v))
        L.append(HEADER_X_POWERED_BY)
        return L

    def header(self, name):
        """Get header by name."""
        key = name.upper()
        if not key in RESPONSE_HEADER_DICT:
            key = name
        return self._headers.get(key)

    def set_header(self, name, value):
        """Set header by given name and value."""
        key = name.upper()
        if not key in RESPONSE_HEADER_DICT:
            key = name
        self._headers[key] = to_str(value)

    @property
    def content_type(self):
        """Get response Content-Type."""
        return self.header('CONTENT_TYPE')

    @content_type.setter
    def content_type(self, value):
        """Set a respose Content-Type."""
        self.set_header('CONTENT_TYPE', value)

    @property
    def content_length(self):
        """Get response Content-Length."""
        return self.header('CONTENT_LENGTH')

    @content_length.setter
    def content_length(self, value):
        """Set response Content-Length."""
        self.set_header('CONTENT_LENGTH', str(value))

    def set_cookie(self, name, value, max_age=None, expires=None, path='/',\
            domain=None, secure=False, http_only=True):
        """Set a cookie with Cookie.SimpleCookie object.
        Args:
            If expires exists, the max_age will be ignore.
            Refer to RFC 2109.
        """
        cookie = Cookie.SimpleCookie()
        cookie[name] = value
        if expires is not None:
            if isinstance(expires, (int, float, long)):
                cookie[name]['expires'] = datetime.datetime.fromtimestamp\
                        (expires, UTC_0).strftime('%a, %Y-%m-%d %H:%M:%S GMT')
            if isinstance(expires, (datetime.date, datetime.datetime)):
                cookie[name]['expires'] = expires.astimezone(UTC_0)\
                        .strftime('%a, %Y-%m-%d %H:%M:%S GMT')
        elif isinstance(max_age, (int, long)):
            cookie[name]['max-age'] = max_age
        cookie[name]['path'] = path
        if domain:
            cookie[name]['domain'] = domain
        if secure:
            cookie[name]['secure'] = secure
        if http_only:
            cookie[name]['httponly'] = http_only
        if not hasattr(self, '_cookies'):
            self._cookies = cookie

    def delete_cookie(self, name):
        """Delete a cookie immediately."""
        self._cookies.clear()

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


def get(path):
    """A decorator for request method 'GET'."""
    def _decorator(func):
        func.__request_route__ = path
        func.__request_method__ = 'GET'
        return func
    return _decorator

def post(path):
    """A decorator for request method 'POST'."""
    def _decorator(func):
        func.__request_route__ = path
        func.__request_method__ = 'POST'
        return func
    return _decorator

def static_file_generator(fpath):
    """Generate a static file."""
    BLOCK_SIZE = 8192
    with open(fpath, 'rb') as f:
        while 1:
            block = f.read(BLOCK_SIZE)
            if not block:
                break
            yield block

RE_STATIC_FILE = re.compile(r'(/static/\w+)')

class Route(object):
    """Mapping URL path info."""
    def __init__(self, func):
        self._path_info = func.__request_route__
        self._response_body = func()

def staticFile(dirname):
    """Mapping static file path info."""
    fpath = os.path.join(ctx.application.document_root, dirname)
    if not os.path.isfile(fpath):
        pass
    ext = os.path.splitext(fpath)[1]
    ctx.response.content_type = mimetypes.types_map(ext.lower(), \
            'application/octet-stream')
    return static_file_generator(fpath)


class Jinja2TempalteEngine(object):
    """Default use jinja2 template engine."""
    def __init__(self, template_dir, **kw):
        from jinja2 import Environment, FileSystemLoader
        if not 'autoescape' in kw:
            kw['autoescape'] = True
        self._env = Environment(loader=FileSystemLoader(template_dir), **kw)

    def add_filter(self, name, func):
        """Add a user-defined filter."""
        self._env.filters[name] = func

    def render(self, template_name, **render_dict):
        """Render template as unicode."""
        template = self._env.get_template(template_name)
        return to_str(template.render(**render_dict))

# global template engine object
template_dir = os.path.join('/home/lastd/AK-Pace/Python/MySite', 'templates')
template = Jinja2TempalteEngine(template_dir)

def _load_module(module_name):
    """Load module from name as str."""
    last_dot = module_name.rfind('.')
    if last_dot == -1:
        return __import__(module_name, globals(), locals(), [])
    from_module = module_name[:last_dot]
    import_module = module_name[last_dot+1:]
    m = __import__(from_module, globals(), locals(), [import_module])
    return getattr(m, import_module)

class App(object):
    """A WSGI application."""
    def __init__(self, document_root):
        self._document_root = os.path.dirname(os.path.abspath(document_root))
        self._static_get = {}
        self._static_post = {}

    def add_url(self, func):
        """From a list add path info and response body."""
        if func.__request_method__ == 'GET':
            self._static_get[func.__request_route__] = func
        if func.__request_method__ == 'POST':
            self._static_post[func.__request_route__] = func

    def add_module(self, module_name):
        """From a module import urls, then add path info and response body."""
        pass

    def run(self, host='localhost', port=9999):
        """Run a local server."""
        from wsgiref.simple_server import make_server
        httpd = make_server(host, port, self.get_app())
        logging.info('Application run at http://%s:%s/' % (host, port))
        httpd.serve_forever()

    def get_app(self):
        """Get WSGI application."""
        _application = Dict(document_root=self._document_root)

        def wsgi(environ, start_response):
            ctx.application = _application
            ctx.request = Request(environ)
            response = ctx.response = Response()
            try:
                path_info = ctx.request.path_info
                request_method = ctx.request.request_method
                # match request method
                if request_method == 'GET':
                    # match path info
                    func = self._static_get.get(path_info, None)
                    if func:
                        response_body = func()
                        response.content_length = len(response_body)
                        print "STATUS: ",response.status
                        start_response(response.status, response.headers)
                        return [response_body]
                if request_method == 'POST':
                    func = self._static_post.get(path_info, None)
                    if func:
                        response_body = func()
                        start_response(response.status, response.headers)
                        return [response_body]
                if path_info.startswith('/static/'):
                    # deal with static file, such as css, js...
                    response_body = staticFile(path_info)
                    start_response(response.status, response.headers)
                    return response_body
            finally:
                del ctx.application
                del ctx.request
                del ctx.response
        return wsgi
