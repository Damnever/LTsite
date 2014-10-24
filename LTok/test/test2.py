#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
--------------------------------------------------------------------------------
    Author: Last_D
    Created Time: 2014-10-16 10:54:51 Thu
    Last Modified: 2014-10-22 22:00:51 Wed
    Description:
        Testing my Web framework.
    Change Activity:
        - None
--------------------------------------------------------------------------------
"""

# add package path
import sys
sys.path.append('../../')

from LTok.web import Page, App, authenticated
import os


class Index(Page):
    """Send data directly."""
    def get(self):
        param = self.request.url_params[0]
        return self.show('<h1 style="text-align:center;">Welcome! %s </h1>'\
                % param)

class Home(Page):
    """Testing template engine."""
    def get(self):
        L = [self.request.path_info, self.request.request_method]
        return self.render('index.html', info_list = L)

class Redirect(Page):
    """Testing redirect method."""
    def get(self):
        self.redirect('/home')

class Talk(Page):
    """Testing post method."""
    def get(self):
        content = self.request.get_argument('content', '')
        return self.render('talk.html', content=content)

    @authenticated
    def post(self):
        content = self.request.get_argument('content', '')
        return self.render('talk.html', content=content)

class Login(Page):
    def get(self):
        return self.render('login.html')
    def post(self):
        name = self.request.get_argument('name', '')
        if name.upper() == 'DXC':
            self.set_current_user(name)
            self.redirect('/talk')
        return self.render('login.html')

app = App(
    [
        ('/(index)?', Index),
        ('/home', Home),
        ('/redirect', Redirect),
        ('/talk', Talk),
        ('/login', Login),
    ],
    template_path = os.path.join(os.path.dirname(__file__), 'templates'),
    static_path = os.path.join(os.path.dirname(__file__), 'static'),
    login_url = '/login',
)

if __name__ == '__main__':
    app.run()
