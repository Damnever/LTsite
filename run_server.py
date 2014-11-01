#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
--------------------------------------------------------------------------------
    Author: Last_D
    Created Time: 2014-10-28 22:10:12 Tue
    Last Modified: 2014-11-01 18:11:14 Sat
    Description:
        Boot loader for my website.
    Change Activity:
        - None
--------------------------------------------------------------------------------
"""

import os
from ConfigParser import ConfigParser
import logging
logging.basicConfig(level=logging.DEBUG)

from LTok.web import App
from LTok.db import init_db
from urls import Index, ArticlePage, Admin, Edit, Login, Signin, Delete
from jinja2_filter import datetime_filter, delta_filter, \
        summary_filter, pwd_filter

conf = ConfigParser()
conf.read('config.ini')

urls = [
    ('/login', Login),
    ('/signin', Signin),
    # all catagory article
    ('/?(\w+)?/', Index),
    # access a article detail
    ('/(\w+)/(\d+)', ArticlePage),
    # manage page include articles, commens , users
    ('/admin/(\w+)', Admin),
    # if match nothing, edit new article else update old article
    ('/admin/edit/(\d+)?', Edit),
    ('/admin/delete/(\w+)/([a-zA-Z0-9]+)', Delete),
]

settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    'login_url': '/login',
}

app = App(urls, **settings)

template = app.get_template_engine()
template.add_filters(datetime_filter=datetime_filter, pwd_filter=pwd_filter,
        delta_filter=delta_filter, summary_filter=summary_filter)

if __name__ == '__main__':
    configs = dict(conf.items('default'))
    init_db(**configs)
    app.run()
