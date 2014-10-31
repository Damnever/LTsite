#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
--------------------------------------------------------------------------------
    Author: Last_D
    Created Time: 2014-10-30 15:54:43 Thu
    Last Modified: 2014-10-31 12:00:41 Fri
    Description:
        Models for users, articles, comments, tags, article_tag.
    Change Activity:
        - None
--------------------------------------------------------------------------------
"""

import time, uuid
from LTok.db import Model, StringField, TextField, IntegerField, BooleanField

def u_id():
    return '%s%018d' % (uuid.uuid4().hex, int(time.time()*100000))

class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, updateable=False, default=u_id, \
            ddl='varchar(50)')
    name = StringField(updateable=False, ddl='varchar(50')
    email = StringField(updateable=False, ddl='varchar(50)')
    password = StringField(ddl='varchar(50)')
    admin = BooleanField()

class Article(Model):
    __table__ = 'articles'

    id = IntegerField(primary_key=True, updateable=False, insertable=False, \
            ddl='integer')
    title = StringField(ddl='varchar(255)')
    content = TextField(ddl='mediumtext')
    raw_content = TextField(ddl='mediumtext')
    author = StringField(ddl='varchar(50)')
    created_at = IntegerField(ddl='integer', default=time.time)
    category = StringField(ddl='varchar(50)')

class Comment(Model):
    __table__ = 'comments'

    id = IntegerField(primary_key=True, updateable=False, insertable=False, \
            ddl='integer')
    article_id = IntegerField(updateable=False, ddl='integer')
    username = StringField(updateable=False, ddl='varchar(50)')
    content = TextField(ddl='mediumtext')
    created_at = IntegerField(ddl='integer', defautlt=time.time)

class Tag(Model):
    __table__ = 'tags'

    id = IntegerField(primary_key=True, updateable=False, insertable=False, \
            ddl='integer')
    tag_name = StringField(ddl='varchar(50)')

class ArticleTag(Model):
    __table__ = 'article_tag'

    id = IntegerField(primary_key=True, updateable=False, insertable=False, \
            ddl='integer')
    article_id = IntegerField(updateable=False, ddl='integer')
    tag_id = IntegerField(ddl='integer')
