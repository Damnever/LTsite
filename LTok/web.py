#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
--------------------------------------------------------------------------------
    Author: Last_D
    Created Time: 2014-10-15 13:31:52 Wed
    Last Modified: 2014-10-28 22:30:20 Tue
    Description:
        A simple WSGI web framework. To re-invent the wheel, just for the
        purpose, better and easier to understand and use others' framework.
    Change Activity:
        - Add PageMetaClass and Page to set url route.
        - Add FileWrapper to convert static file into an iterable.
        - Add a App class. The core of framework. And I found that I'm any
        different from the walking dead.
        - Fix The errors, because the called function not return a value:
            `AttributeError: 'NoneType' object has no attribute 'split'`
            `TypeError: 'NoneType' object is not iterable`
        - Fix the error, the page would loading forever when handling POST
        request, because I don't pass a `size` parameter to the `read` method
        of `environ['wsgi.input']` object.
            `^C` will raises `error: [Errno 32] Broken pipe`.
        - Fix error when redirect to new url and add a middle page for manual
        redirection.
--------------------------------------------------------------------------------
"""

from http import Request, Response, HttpError, RedirectError

from tools import to_str

from abc import ABCMeta, abstractmethod

import threading, logging, os.path, mimetypes, re, time, hmac, uuid

"""A global variable can get request info and set response info."""
g = threading.local()

class PageMetaClass(type):
    """
    Metaclass for route, which can add some class attribute into subclass,
    which is derived from Page.
    """
    def __new__(cls, name, bases, attrs):
        if name == 'Page':
            return type.__new__(cls, name, bases, attrs)
        if 'request_method' not in attrs:
            attrs['request_method'] = []
        if 'get' in attrs:
            attrs['request_method'].append('GET')
        if 'post' in attrs:
            attrs['request_method'].append('POST')
        return type.__new__(cls, name, bases, attrs)


# global variable, which is a template engine object
_G_template = None

# global variable, which is a session secret key
_G_secret = None

# global variable, which is a cookie name
_G_cookie_name = None


def _make_single_cookie(u_id, max_age):
    """make a single cookie value, use hmac."""
    expires = str(int(time.time()) + max_age)
    L = [u_id, expires, hmac.new(_G_secret, 'LTok%s-%s' % \
            (u_id, expires)).hexdigest()]
    print 'Set L:', L
    return '-'.join(L)

def _parse_single_cookie(cookie_str):
    """parse single cookie, which is made."""
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        print 'GET L: ', L
        u_id, expires, hmac_str = L
        if int(expires) < time.time():
            return None
        if hmac_str != hmac.new(_G_secret, 'LTok%s-%s' % \
                (u_id, expires)).hexdigest():
            return None
        return u_id
    except:
        return None

class Page(object):
    """
    Route mapping url info

    >>> class Index(Page):
    ...     def get(self):
    ...         print "I'm implemented!"
    ...
    >>> print Index.request_method
    ['GET']
    >>> i = Index()
    >>> i.get()
    "I'm implemented!"
    >>> i.post()
    Traceback (most recent call last):
        ...
    NotImplementedError: method 'post' not implemented.
    """
    __metaclass__ = PageMetaClass

    def get(self):
        """Override this method can set request method to 'GET'."""
        raise NotImplementedError("method 'get' not implemented.")

    def post(self):
        """Override this method can set request method to 'POST'."""
        raise NotImplementedError("method 'post' not implemented.")

    @property
    def request(self):
        """Get the request object, which is contains some request info."""
        return g.request

    @property
    def response(self):
        """Get the Response object, which can set some response info,
        such as cookie."""
        return g.response

    def get_current_user(self):
        """Get session(cookie)"""
        cookie_value = self.get_cookie(_G_cookie_name)
        print 'GET cookie', cookie_value
        if cookie_value is None:
            return None
        u_id = _parse_single_cookie(cookie_value)
        return u_id

    def set_current_user(self, u_id, max_age=86400):
        """In fact, this operation will set a session cookie."""
        cookie_value = _make_single_cookie(u_id, max_age)
        self.set_cookie(_G_cookie_name, cookie_value)

    def redirect(self, url):
        """Redirect to a location."""
        raise RedirectError(303, url)

    def set_cookie(self, name, value, max_age=(8*60*60), expires=None, \
            path='/', domain=None, secure=False, http_only=True):
        """Set a cookie by Response object and current_user."""
        self.response.set_cookie(name, value, max_age, expires, path, domain,\
                secure, http_only)

    def get_cookie(self, name):
        """Get cookie value by name and Request object."""
        cookies =  self.request.cookies
        if not cookies:
            return None
        return cookies.get(name)

    def show(self, data):
        """Send data to page directly."""
        return to_str(data)

    def render(self, template_name, **kwargs):
        """Render the html file by template engine, default to jinja2."""
        from jinja2 import TemplateNotFound
        try:
            return _G_template.render(template_name, **kwargs)
        except TemplateNotFound:
            logging.warning("-- Template path default to 'templates' of \
                    current directory, you should make a directory \
                    'templates' in current directory or given specific \
                    template path in dict `settings`.")
            raise TemplateNotFound(template_name)


# decorator
import functools

def authenticated(func):
    """A authenticated decorator, detecting user if login when accessing the
    page, redirecting to login url if not.
    """
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        self = args[0]
        if self.get_current_user():
            return func(*args, **kwargs)
        else:
            raise RedirectError(303, 'login_url')
    return _wrapper


class Method(object):
    """Dividing the urls mapping into two dict, one dict's request method
    is GET, another is POST.
    """
    def __init__(self, urls):
        self._urls = dict(urls)

    def dict_for_get(self):
        dget = dict()
        for k, v in self._urls.iteritems():
            if 'GET' in v.request_method:
                # compile regular expression
                re_k = re.compile('^' + k + '$')
                dget[re_k] = v
        return dget

    def dict_for_post(self):
        dpost = dict()
        for k, v in self._urls.iteritems():
            if 'POST' in v.request_method:
                re_k = re.compile('^' + k + '$')
                dpost[re_k] = v
        return dpost

    def __call__(self):
        dget = self.dict_for_get()
        dpost = self.dict_for_post()
        return (dget, dpost)


class Template(object):
    """Use other template engine must inherited from this class."""
    __metaclass__ = ABCMeta

    def __init__(self, template_dir, **kw):
        """Init template engine."""
        pass

    @abstractmethod
    def render(self, template_name, **kw):
        """Render the template file and return data as UTF-8."""
        return _G_template.render(template_name, **kw)


class Jinja2TemplateEngine(Template):
    """Template engine default to Jinja2."""
    def __init__(self, template_dir, **kw):
        from jinja2 import Environment, FileSystemLoader
        if not 'autoescape' in kw:
            kw['autoescape'] = True
        self._env = Environment(loader=FileSystemLoader(template_dir), **kw)

    def add_filter(self, name, func):
        """Add filter function."""
        self._env.filters[name] = func

    def add_filters(self, **filters):
        """Add more than one filters."""
        for name, func in filters.iteritems():
            self.add_filter(name, func)

    def render(self, template_name, **kw):
        template = self._env.get_template(template_name)
        return to_str(template.render(**kw))

def static_file_generator(fpath, buffer_size=8192):
    """Convert a file into an iterable."""
    with open(fpath, 'rb') as f:
        while 1:
            block = f.read(buffer_size)
            if not block:
                break
            yield block


class App(object):
    """
    App object will done with some configuration.

    Note:
        Template engine default to Jinja2. However, you can use other
    template engine, so you must inherit a subclass from class Template,
    and use set_template_engine() to add your template engine.
    """

    def __init__(self, urls, **settings):
        """
        Parameters:
         - urls: a dict mapping path info and subclass of class Route.
         - settings: A dict maybe contain the following variables:
           - template_path: the template engine needed template directory,
           default to `templates`.
           - static_path: the static file directory, default to `static`.
           - not_found_page: a url indicate 404 page, which is a subclass of
           Page.
           - other_error_page: a url indicate other HTTP error. which is a
           subclass of Page.
        """
        # urls dict
        self._urls = dict(urls)

        # template path and set template engine
        if not settings.get('template_path', None):
            template_path = 'templates'
        else:
            template_path = settings['template_path']
        self.set_template_engine(Jinja2TemplateEngine, template_path)

        # static file path and root path
        if not settings.get('static_path', None):
            static_path = 'static'
            self._document_root = os.path.abspath('./')
        else:
            static_path = settings['static_path']
            self._document_root = os.path.split(os.path.abspath(static_path))[0]
        self._static_path = static_path

        # login_url
        if settings.get('login_url', None):
            self._login_url = settings['login_url']
        # error page
        if settings.get('not_found_page', None):
            self._not_found_page = settings['not_found_page']
        if settings.get('other_error_page', None):
            self._other_error_page = settings['other_error_page']

        # session secret_key
        global _G_secret
        if settings.get('secret_key', None):
            _G_secret = str(settings['secret_key'])
        else:
            _G_secret = str(uuid.uuid4())

        # cookie name
        global _G_cookie_name
        if settings.get('cookie_name', None):
            _G_cookie_name = settings['cookie_name']
        else:
            _G_cookie_name = '_xsrf_'

        # set logging level
        self.set_log_level()

    def set_template_engine(self, cls, template_dir, **kw):
        """
        Set a template Engine. The App's constructor will initialize the default
        template engine, Jinja2.

        Parameters:
         - cls: the class name, which is subclass of Template.
         - template_dir: also seeing the App constructor, same as template_path.
         - kw: some configs to initialize your template engine.
        """
        global _G_template
        if cls.__name__ == 'Jinja2TemplateEngine':
            _G_template = Jinja2TemplateEngine(template_dir, **kw)
        else:
            _G_template = cls(template_dir, **kw)

    def get_template_engine(self):
        """Get template object."""
        return _G_template

    def _get_static_file_prefix(self):
        """Get prefix of static file diretory."""
        if self._static_path == 'static':
            return '/static'
        return os.path.split(self._static_path)[1]

    def set_log_level(self, level=logging.INFO):
        """
        Set log level to show logging information, default to 20.
        Your choices:
        10(logging.DEBUG), 30(logging.WARNING), 40(logging.CRITICAL).
        """
        if level not in [10, 20, 30, 40]:
            logging.warning('-- The `level` parameter should be \
                10(logging.DEBUG) 20(logging.INFO) 30(logging.WARNING) \
                40(logging.CRITICAL)')
            return
        logging.basicConfig(level=logging.INFO)

    def run(self, port=9999, host='localhost'):
        """Run a local server, which will work in local area network."""
        if not isinstance(host, str):
            logging.warning('-- The `host` parameter should be str object.')
            return
        if not isinstance(port, int):
            logging.warning('-- The `port` parameter should be int object.')
            return
        from wsgiref.simple_server import make_server
        logging.info('-- The Server run at http://%s:%s/\n' % (host, port)\
                + '-'*60)
        httpd = make_server(host, port, self.get_app())
        httpd.serve_forever()

    def wrap_file(self, path, buffer_size=8192):
        """Wraps a file."""
        fpath = os.path.join(self._document_root, path[1:])
        if not os.path.isfile(fpath):
            raise HttpError(404)
        ext = os.path.splitext(fpath)[1]
        if ext == '.ico':
            g.response.content_type = 'image/x-icon'
        else:
            g.response.content_type = mimetypes.types_map.get(ext.lower(),\
                'application/octet-stream')
        g.response.content_length = os.path.getsize(fpath)
        return static_file_generator(fpath, buffer_size)

    def _handle_response(self, path_info, start_response):
        """Handle normal request by path info."""
        request_method = g.request.request_method
        method_get, method_post = Method(self._urls)()
        # deal with redirect
        if g.response.status.startswith('3'):
            from cgi import escape
            data = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
            '<head><title>Redirecting...</title></head>\n'
            '<div style="text-align:center;"><h1>Redirecting...</h1>\n'
            '<p>You should be redirected automatically to target URL:\n'
            '<a href="%s">%s</a>. If not click the link.</div>\n' % \
                    (escape(path_info), path_info)
            g.response.content_length = len(data)
            g.response.location = 'http://' + g.request.host + path_info
            start_response(g.response.status, g.response.headers)
            return [data]
        # deal with GET request
        if request_method == 'GET':
            page = self._get_page_obj(path_info, method_get)
            if page:
                data = page().get()
                g.response.content_length = len(data)
                start_response(g.response.status, g.response.headers)
                return [data]
        # deal with POST request
        if request_method == 'POST':
            page = self._get_page_obj(path_info, method_post)
            if page:
                data = page().post()
                g.response.content_length = len(data)
                start_response(g.response.status, g.response.headers)
                return [data]
        # deal with icon
        if path_info.startswith('/favicon'):
            data = self.wrap_file(path_info)
            start_response(g.response.status, g.response.headers)
            return data
        # deal with static file
        if path_info.startswith(self._get_static_file_prefix()):
            data = self.wrap_file(path_info)
            start_response(g.response.status, g.response.headers)
            return data
        raise HttpError(404)

    def _get_page_obj(self, path_info, method_d):
        """Get Page object."""
        for re_url in method_d.iterkeys():
            # path_info matching url
            match = re_url.match(path_info)
            if match:
                match_group = match.group()
            else:
                continue
            # if matched url equals path_info
            if match_group == path_info:
                # search regex group from url
                url_params = re_url.findall(path_info)
                if url_params:
                    g.request.url_params = url_params
                page = method_d.get(re_url, None)
                return page
        return None

    def get_app(self):
        """Get an application for WSGI server."""
        def _wsgi(environ, start_response):
            """A application for WSGI server."""
            global g
            g.request = Request(environ)
            g.response = Response()
            path_info = g.request.path_info

            # deal with normal page
            try:
                return self._handle_response(path_info, start_response)
            # deal with redirection
            except RedirectError as e:
                if e.location == 'login_url':
                    if hasattr(self, '_login_url'):
                        url = self._login_url
                    else:
                        logging.warning('-- You should set `login_url` in \
                                settings dict.')
                        raise HttpError(404)
                else:
                    url = e.location
                g.response.status = e.status
                #g.response.location = 'http://' + g.request.host + url
                return self._handle_response(url, start_response)
            # deal with bad request
            except HttpError as e:
                if hasattr(self, '_not_found_page'):
                    url = self._not_found_page
                    g.response.status = e.status
                    return self._handle_response(url, start_response)
                else:
                    # add all urls later.
                    data = """<html>
                    <head>
                        <title>404</title>
                        <style type="text/css">
                            body {
                                margin: 0 auto;
                                width: 50%;
                                font-family: "Hiragino Sans GB",
                                "Microsoft YaHei","WenQuanYi Micro Hei",
                                sans-serif;
                            }
                            .bd {
                                margin: 10% auto;
                                border: 1px solid #696969;
                                background: #696969;
                                border-radius: 5px;
                            }
                            p {
                                color: #fff;
                                font-size: 43px;
                                font-weight: bold;
                                text-align: center;
                                text-shadow: 0 0 5px #fefcc9, 3px -3px 5px
                                #feec85, -5px -5px 10px #ffae34, 5px -10px
                                13px #ec760c, -5px -15px 15px #cd4606, 0
                                -20px 18px #973716, 3px -23px 20px #451b0e;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="bd">
                            <p>Oh, God! The page Not Found!</p>
                        </div>
                    </body>
                    </html>
                    """
                start_response(e.status, g.response.headers)
                return [data]
            finally:
                del g.request
                del g.response
        return _wsgi
