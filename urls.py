#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
--------------------------------------------------------------------------------
    Author: Last_D
    Created Time: 2014-10-28 21:03:51 Tue
    Last Modified: 2014-11-01 20:02:04 Sat
    Description:
        All URLs for my website.
    Change Activity:
        - None
--------------------------------------------------------------------------------
"""

import time, hashlib

from LTok.web import Page
from LTok.web import authenticated, make_single_cookie
from LTok.http import RedirectError

import markdown2

from models import User, Article, Comment, Tag, ArticleTag


def encrpt_password(password):
    md = hashlib.md5(password).hexdigest()
    result = hashlib.sha1(md).hexdigest()
    return result

import functools
def admin(func):
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        self = args[0]
        u_id = self.get_current_user()
        if not u_id:
            raise RedirectError(303, '/login')
        user = User.get_by_primary_key(u_id)
        if not user.admin:
            raise RedirectError(303, '/index/')
        return func(*args, **kwargs)
    return _wrapper

class Login(Page):

    def get(self):
        return self.render('login.html')

    def post(self):
        data =  self.request.data(username='', password='', rememberme='')
        print data.username, data.password
        if not data.username:
            pass
        if not data.password:
            pass
        user = User.select_one('name=?', data.username)
        print user.name, user.password
        if user.name == data.username and \
                user.password == encrpt_password(data.password):
            if data.rememberme == 'true':
                max_age = (7*24*60*60*60) # a week
                cookie_value = make_single_cookie(user.id, max_age)
                self.set_cookie('_xsrf_', cookie_value, max_age=max_age)
            else:
                self.set_current_user(user.id)
            self.redirect('/index/')
        else:
            return self.render('login.html')

class Signin(Page):

    def get(self):
        return self.render('signin.html')

    def post(self):
        data = self.request.data(username='', password='', repassword='', email='')
        username = data.username
        password = data.password
        repassword = data.repassword
        email = data.email.strip().lower()
        if not username:
            pass
        if not password:
            pass
        if not repassword:
            pass
        if not data.email:
            pass
        if password != repassword:
            pass
        if User.select_one('name=?', username):
            pass
        if User.select_one('email=?', email):
            pass
        user = User(name=username, password=encrpt_password(password), \
                email=email)
        user.insert()
        self.redirect('/login')

class Index(Page):
    """
    Index page that will be used to display content according to navigation.
    """
    def get(self):
        nav = self.request.url_params
        if nav == 'index' or not nav:
            articles = Article.select_all(None)
        elif nav in ['coding', 'wiki', 'bushit']:
            articles = Article.select_all('category=?', nav)
        elif nav == 'about':
            comments = Comment.select_all('article_id=?', 222222222)
            return self.render('about.html', comments=comments)
        else:  # according to tag
            tag_id = Tag.select_one('tag_name=?', nav)
            article_tags = ArticleTag.select_all('tag_id=?', tag_id.id)
            conditions = ' or '.join(['id=?' for a in article_tags])
            args = [a.article_id for a in article_tags]
            articles = Article.select_all(conditions, *args)
        # all tags
        d_tags = Tag.select('select tag_name from tags')
        if d_tags:
            tags = [tag for d in d_tags for tag in d.itervalues()]
        else:
            tags = None
        return self.render('toc.html', tags=tags, articles=articles)

    @authenticated
    def post(self):
        """Comment for about page."""
        comment = self.request.get_argument('comment', '')
        # insert into db, and load page again
        u_id = self.get_current_user()
        user_d = User.select_one('id=?', u_id)
        created_at = int(time.time())
        comment_d = Comment(article_id=222222222, username=user_d.name, \
                content=comment, created_at=created_at)
        comment_d.insert()
        comments = Comment.select_all('article_id=?', 222222222)
        return self.render('about.html', comments=comments)

class ArticlePage(Page):
    """Searching article according to article created time."""
    def get(self):
        created_at = int(self.request.url_params[1])
        article = Article.select_one('created_at=?', created_at)
        if article:
            comments = Comment.select_all('article_id=?', article.id)
        else:
            comments = None
        return self.render('article.html', title=article.title, article=article,\
                comments=comments)

    @authenticated
    def post(self):
        created_at = int(self.request.url_params[1])
        article = Article.select_one('created_at=?', created_at)
        comment = self.request.get_argument('comment', '')
        # insert into db, and load page again
        u_id = self.get_current_user()
        user = User.select_one('id=?', u_id)
        created_at = int(time.time())
        comment_d = Comment(article_id=article.id, username=user.name, \
                content=comment, created_at=created_at)
        comment_d.insert()
        comments = Comment.select_all('article_id=?', article.id)
        return self.render('article.html',title=article.title, article=article,\
                comments=comments)

class Admin(Page):
    """Admin page and need permission."""
    @admin
    def get(self):
        nav = self.request.url_params
        if nav == 'articles':
            articles = Article.select_all(None)
            return self.render('_admin.html', articles=articles)
        elif nav == 'comments':
            comments = Comment.select_all(None)
            return self.render('_comments.html', comments=comments)
        elif nav == 'users':
            users = User.select_all(None)
            return self.render('_users.html', users=users)

    @admin
    def post(self):
        """Edit Artilce."""
        data = self.request.data(title='', tag='', category='', \
                raw_content='', old_tag='', created_at='')
        created_at = data.created_at
        title = data.title
        old_tag = data.old_tag
        tag = data.tag
        category = data.category
        raw_content = data.raw_content
        content = (markdown2.markdown(raw_content)).encode('utf-8')
        u_id = self.get_current_user()
        admin = User.get_by_primary_key(u_id)
        created_at_now = int(time.time())
        # new article
        if not created_at:
            article = Article(title=title,content=content,\
                    raw_content=raw_content,category=category, \
                    author=admin.name, created_at=created_at_now)
            article.insert()
            new_article = Article.select_one('created_at=?', created_at_now)
            article_id = new_article.id
            # tag
            tag_d = Tag.select_one('tag_name=?', tag)
            # tag doesn't exists
            if not tag_d:
                new_tag = Tag(tag_name=tag)
                new_tag.insert()
                get_tag = Tag.select_one('tag_name=?', tag)
                tag_id = get_tag.id
            # tag exists
            else:
                tag_id = tag_d.id
            article_tag = ArticleTag(article_id=article_id, tag_id=tag_id)
            article_tag.insert()
        # update old article
        else:
            article = Article(title=title, content=content, \
                    raw_content=raw_content, author=admin.name, \
                    category=category, created_at=created_at_now)
            article.update('created_at=?', created_at)
            new_article = Article.select_one('created_at=?', created_at_now)
            article_id = new_article.id
            old_tag = Tag.select_one('tag_name=?', old_tag)
            new_tag = Tag(tag_name=tag)
            other_article_tag = ArticleTag.select_all('tag_id=?', old_tag.id)
            # other article doesn't have this article
            if len(other_article_tag) >= 1:
                tag_id = old_tag.id
                new_tag.update('id=?', tag_id)
            # other article has this tag
            else:
                new_tag.insert()
                get_tag = Tag.select('tag_name=?', tag)
                tag_id = get_tag.id
            article_tag = ArticleTag(tag_id=tag_id)
            article_tag.update('article_id=?', article_id)
        self.redirect('/admin/articles')


class Edit(Page):
    """Publish or update article."""
    @admin
    def get(self):
        created_at = self.request.url_params
        if created_at:
            article = Article.select_one('created_at=?', int(created_at))
            title = article.title
            tag_id_dict = ArticleTag.select_one('article_id=?', article.id)
            tag_name_dict = Tag.select_one('id=?', tag_id_dict.tag_id)
            tag = tag_name_dict.tag_name
        else:
            title = None
            tag = None
            article = None
        return self.render('_edit.html', title=title, tag=tag, \
                article=article, created_at=created_at)


class Delete(Page):
    """Display deleted info."""
    @admin
    def get(self):
        params = self.request.url_params
        print params
        category = params[0]
        which = params[1]
        article, comment, comments, user = None, None, None, None
        if category == 'article':
            # delete article and all related comments
            old_article = Article.select_one('created_at=?', which)
            article = old_article
            old_article.delete()
            old_comments = Comment.select_all('article_id=?', article.id)
            comments = old_comments
            if old_comments:
                for comment in old_comments:
                    comment.delete()
        elif category == 'user':
            old_user = User.select_one('id=?', which)
            user = old_user
            old_user.delete()
        elif category == 'comment':
            old_comment = Comment.select_one('id=?', which)
            comment = old_comment
            old_comment.delete()
        return self.render('_delete.html', article=article, comment=comment, \
                comments=comments, user=user)
