#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
--------------------------------------------------------------------------------
    Author: Last_D
    Created Time: 2014-10-23 11:29:22 Thu
    Last Modified: 2014-10-24 22:42:31 Fri
    Description:
        Some use-defined Jinja2 filter.
    Change Activity:
        - Fix the error, use a “mutable” object as a default value, like list.
--------------------------------------------------------------------------------
"""

import datetime, time, HTMLParser, re

def datetime_filter(value, format='%Y-%m-%d %H:%M:%S %a'):
    """
    >>> d = datetime_filter(1414040820.77917)
    >>> d
    '2014-10-23 13:07:00 Thu'
    """
    if isinstance(value, (float, int, long)):
        value = datetime.datetime.fromtimestamp(value)
    return value.strftime(format)

def delta_filter(t):
    """
    like that:
        delta = delta_filter(1414040820.77917)
        delta # u'2分钟前'
    """
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta//60)
    if delta < 86400:
        return u'%s小时%s分钟前' % ((delta//3600 ), (delta % 3600/60))
    if delta < 604800:
        return u'%s天%s小时前' % ((delta//86400), (delta % 86400/3600))
    dt = datetime.datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


def _get_plain_text(html, l=None):
    """Get all plain text from html body."""

    if l is None:
        l = []

    class MyHTMLParser(HTMLParser.HTMLParser):
        """Process arbitrary data."""
        def handle_data(self, data):
            l.append(data.strip())

    body = re.search(r'<body>.+?</body>', html)
    if body:
        body = body.group()
    body = html
    parser = MyHTMLParser()
    parser.feed(body)
    return ' '.join(l)

def summary_filter(content):
    """Get summary from content, at least 230 letters."""
    data = _get_plain_text(content)
    percent_len = len(data) // 5
    summary_len = 230 if percent_len < 230 else percent_len
    return data[:summary_len] + ' ... ...'
