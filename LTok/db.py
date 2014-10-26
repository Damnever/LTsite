#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
--------------------------------------------------------------------------------
    Author: Last_D
    Created Time: 2014-10-25 11:10:37 Sat
    Last Modified: 2014-10-26 20:04:04 Sun
    Description:
        A module for operating database, include a ORM framework.
        -> https://github.com/michaelliao/transwarp/blob/master/transwarp/db.py
    Change Activity:
        - None
--------------------------------------------------------------------------------
"""

from tools import Dict

import functools, threading, logging

class InterfaceError(Exception):
    pass

class DatabaseError(Exception):
    pass

class ProgrammingError(DatabaseError):
    pass

class MultiColumnError(DatabaseError):
    pass

# A global engine object holds MySQLdb connect handler.
engine = None

class _Engine(object):

    def __init__(self, connect):
        self._connect = connect

    def get_connect(self):
        return self._connect

def init_db(user, passwd, db, host='localhost', port=3306, **kwargs):
    """Create a MySQLdb engine with some parameters."""
    import MySQLdb
    global engine
    if engine is not None:
        raise DatabaseError('Engine is already initialized.')
    params = dict(user=user, password=passwd, database=db, host=host, port=port)
    defaults = dict(use_unicode=True, charset='utf8', \
            collation='utf8_general_ci', autocommit=False, buffered=True)
    params.update(defaults)
    del defaults
    params.update(kwargs)
    try:
        engine = _Engine(lambda: MySQLdb.connect(**params))
        logging.info('Init mysql engine <%s> done.' % hex(id(engine)))
    except:
        raise InterfaceError('Init database failed.')


class _DBContext(threading.local):
    """Thread local object that holds connection info."""
    def __init__(self):
        self.connection = None
        self.transactions = 0

    def is_init(self):
        return not self.connection is None

    def init(self):
        if self.connection is None:
            logging.debug('Open connection ...')
            self.connection = engine.get_connect()
        self.trasactions = 0

    def cursor(self):
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def cleanup(self):
        if self.connection:
            logging.debug('Close connection ...')
            self.connection.close()
            self.connection = None

_db_context = _DBContext()

class _ConnectionCtx(object):
    """
    _ConnectionCtx object that can open and close connection context.
    _ConnectionCtx object can be nested and only the most outer connection
    has effect.
    """
    def __enter__(self):
        global _db_context
        self.should_cleanup = False
        if not _db_context.is_init():
            _db_context.init()
            self.should_cleanup = True
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        global _db_context
        if self.should_cleanup:
            _db_context.cleaup()

def connection():
    """
    Return a _ConnectionCtx object that can be used by with statement.
    """
    return _ConnectionCtx()

def with_connection(func):
    """Decorator for connection."""
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        with connection():
            return func(*args, **kwargs)
    return _wrapper

class _TransactionCtx(object):
    """
    _TransationCtx object that can handle transactions.
    """
    def __enter__(self):
        global _db_context
        self.should_close_conn = False
        if not _db_context.is_init():
            _db_context.init()
            self.should_close_onn = True
        _db_context.transactions += 1
        logging.debug('Begining transation ...' if _db_context.transactions==1\
                else 'Join to current transactions ...')
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        global _db_context
        _db_context.transactions -= 1
        try:
            if _db_context.transactions == 0:
                if exc_type is None:
                    self.commit()
                else:
                    self.rollback()
        finally:
            if self.should_close_conn:
                _db_context.cleanup()

    def commit(self):
        global _db_context
        logging.debug('Commit transation ...')
        try:
            _db_context.commit()
            logging.debug('Commit done.')
        except:
            logging.warning('Commit failed, try rollbak ...')
            _db_context.rollback()
            logging.warning('Rollback done.')
            raise

    def rollback(self):
        global _db_context
        logging.debug('Rollback transaction ...')
        _db_context.rollback()
        logging.info('Rollback done.')

def transaction():
    """Return _TransactionCtx that can use with statement."""
    return _TransactionCtx()

def with_transaction(func):
    """A decorator that makes function around transation."""
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        with transaction():
            return func(*args, **kwargs)
    return _wrapper


def _select(sql, one, *args):
    """
    Execute select SQL and return unique result or list result,
    according to one(True or False).
    """
    global _db_context
    logging.debug('SQL: %s, ARGS: %s' % (sql, args))
    try:
        cursor = _db_context.cursor()
        cursor.execute(sql, args)
        if cursor.description:
            # first arg of description is column name.
            names = [x[0] for x in cursor.description]
        if one:
            values = cursor.fetchone()
            if not values:
                return None
            return Dict(names, values)
        return [Dict(names, x) for x in cursor.fetchall()]
    finally:
        if cursor:
            cursor.close()

@with_connection
def select_one(sql, *args):
    """Execute select SQL and return one result."""
    return _select(sql, True, *args)

@with_connection
def select_int(sql, *args):
    """Execute select SQL and return a int reslut.
    Such as [select count(`user`) from users]."""
    d = _select(sql, True, *args)
    if len(d) != 1:
        raise MultiColumnError('Except only one column.')
    return d.values()[0]

@with_connection
def select(sql, *args):
    """Execute select SQL and return list or empty list if no result."""
    return _select(sql, False, *args)

def _update(sql, args):
    """Such as [update users set name='Last_D']"""
    global _db_context
    logging.debug('SQL: %s, ARGS: %s' % (sql, args))
    try:
        cursor = _db_context.cursor()
        cursor.excute(sql, args)
        row_count = cursor.rowcount
        if _db_context.transactions == 0:
            logging.debug('Auto commit.')
            _db_context.commit()
        return row_count
    finally:
        if cursor:
            cursor.close()

@with_connection
def insert(table, **kwargs):
    """Execute insert SQL."""
    cols, args = zip(*kwargs.iteritems())
    sql = 'insert into %s (%s) values(%s)' % (table, ','.join(cols), \
            ','.join('?' for i in range(len(args))))
    return _update(sql, args)

@with_connection
def update(sql, *args):
    """Execute update SQL."""
    return _update(sql, *args)

@with_connection
def update_kw(table, conditions, *args, **kwargs):
    """Execute update SQL, according to conditions.

    Parameters:
        table: table name.
        conditions: conditions, such as `'id=? or id=?'`, which can be None.
        args: args for conditions, such as `1, 2`.
        kwargs: column name and value pairs, such as `name='Last_D'`
    """
    if len(kwargs) == 0:
        raise ValueError('No keyword args.')
    sqls = ['update', table, 'set']
    params = []
    updates = []
    for column, value in kwargs.iteritems():
        updates.append('%s=?' % column)
        params.append(value)
    sqls.append(', '.join(updates))
    sqls.append('where')
    sqls.append(conditions)
    sql = ' '.join(sqls)
    params.extend(args)
    return _update(sql, *params)

@with_connection
def delete(table, conditions, *args):
    """Execute delete SQL.
    Parameters:
        table: table name.
        conditions: such as `id=? and name=?`.
        args: arguments for conditions, such as `1, 'Last_D'`.
    """
    sql = 'delete from %s where %s' % (table, conditions)
    return _update(sql, *args)


class Field(object):

    _count = 0

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', None)
        self._default = kwargs.get('default', None)
        self.primary_key = kwargs.get('primary_key', False)
        self.nullable = kwargs.get('nullable', False)
        self.updateable = kwargs.get('updateable', True)
        self.insertable = kwargs.get('insertable', True)
        self.ddl = kwargs.get('ddl', '')

        self.order = Field._count
        Field._count += 1

    @property
    def default(self):
        d = self._default
        return d() if callable(d) else d

class StringField(Field):

    def __init__(self, **kwargs):
        if not 'default' in kwargs:
            kwargs['default'] = ''
        if not 'ddl' in kwargs:
            kwargs['ddl'] = 'varchar(255)'
        super(StringField, self).__init__(**kwargs)

class TextField(Field):

    def __init__(self, **kwargs):
        if not 'default' in kwargs:
            kwargs['default'] = ''
        if not 'ddl' in kwargs:
            kwargs['ddl'] = 'text'
        super(TextField, self).__init__(**kwargs)

class IntegerField(Field):

    def __init__(self, **kwargs):
        if not 'default' in kwargs:
            kwargs['default'] = 0
        if not 'ddl' in kwargs:
            kwargs['ddl'] = 'int'
        super(IntegerField, self).__init__(**kwargs)

class FloatField(Field):

    def __init__(self, **kwargs):
        if not 'default' in kwargs:
            kwargs['default'] = 0.0
        if not 'ddl' in kwargs:
            # if not real as float, real will be double precision.
            kwargs['ddl'] = 'real'
        super(FloatField, self).__init__(**kwargs)

class BooleanField(Field):

    def __init__(self, **kwargs):
        if not 'default' in kwargs:
            kwargs['default'] = False
        if not 'ddl' in kwargs:
            kwargs['ddl'] = 'bool'
        super(BooleanField, self).__init__(**kwargs)

class BlobField(Field):

    def __init__(self, **kwargs):
        if not 'default' in kwargs:
            kwargs['default'] = ''
        if not 'default' in kwargs:
            kwargs['ddl'] = 'blob' # 64k
        super(BlobField, self).__init__(**kwargs)


def _gen_sql(table, mappings):
    """Generate SQL statement.
    Such as:
        create table users (
            `id` int not null.
            `name` varchar(25) not null,
            primary_key (`id`)
        );
    """
    primary_key = None
    sql = ['create table %s (' % table]
    for f in sorted(mappings.itervalues(), lambda x,y: cmp(x.order,y.order)):
        if not hasattr(f, 'ddl'):
            raise ProgrammingError("No ddl in field '%s'" % f.name)
        if f.primary_key:
            primary_key = f.name
        sql.append(f.nullable and '    %s %s,' % (f.name, f.ddl) or \
                '    %s %s not null,' (f.name, f.ddl))
    sql.append('primary key (%s)' % primary_key)
    sql.append(');')
    return '\n'.join(sql)

class ModelMetaClass(type):
    """
    Metaclass for model.
    """
    def __new__(cls, name, bases, attrs):
        # skip base Model class
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)

        # store all subclass info
        if not hasattr(cls, 'subclasses'):
            cls.subclasses = {}
        if not name in cls.subclasses:
            cls.subclasses[name] = name
        else:
            logging.warning('Redefine class: %s' % name)

        logging.info('Scan Object Relational Mapping %s ...' % name)
        mappings = dict()
        primary_key = None
        for k, v in attrs.iteritems():
            if isinstance(v ,Field):
                if not v.name:
                    v.name = k
                logging.info('Found mappings: %s => %s' % (k, v))
                # check duplicate primary key
                if v.primary_key:
                    if primary_key:
                        raise ProgrammingError("Cannot defined more than one primary \
                                key in class: '%s'." % name)
                    if v.updateable:
                        logging.warning('Note: change primary key to non-updateable.')
                        v.updateable = False
                    if v.nullable:
                        logging.warning('Note: change primary key to non-nullable.')
                        v.nullable = False
                    primary_key = v.name
                mappings[k] = v
        # check exists of primary key
        if not primary_key:
            raise ProgrammingError("Primary key not in class: '%s'" % name)
        for k in attrs:
            attrs.pop(k)
        attrs['__table__'] = name.lower()
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primary_key
        def _sql(self):
            return _gen_sql(name.lower(), mappings)
        attrs['__sql__'] = _sql
        return type.__new__(cls, name, bases, attrs)

class Model(dict):
    """
    Base class for ORM.

    Example:
        class User(Model):
            id = IntegerField(primary_key=True)
            name = StringField()
            email = StringField()
    """
    __metaclass__ = ModelMetaClass

    def __init__(self, **kwargs):
        super(Model, self).__init__(**kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    @classmethod
    def get_by_primary_key(cls, primary_key):
        """Execute select SQL by primary key."""
        d = select_one('select * from {0} where {1}=?'.format(cls.__table__, \
                cls.__primary_key__.name), primary_key)
        return cls(**d) if d else None

    @classmethod
    def select_one(cls, conditions, *args):
        """
        Execute select SQL and return first one result.

        Parameters:
            conditions: such as `id=?` or None.
            argss: args for conditions, such as `1` or nothing.
        """
        if conditions:
            d = select_one('select * from {0} where {1}'.format(cls.__table__, \
                    conditions), *args)
        else:
            d = select_one('select * from %s' % cls.__table)
        return cls(**d) if d else None

    @classmethod
    def count(cls, conditions, *args):
        """Count rows of the table by conditions or not, then return a
        number. Parameters `args` for conditions if exists.
        """
        if conditions:
            num = select_int('select count({0}) from {1} where {2}'.format(\
                cls.__primary__key__.name, cls.__table__, conditions), *args)
        else:
            num = select_int('select count({0}) from {1}'.format(\
                    cls.__primary_key__.name, cls.__table__))
        return num

    def update(self):
        kw = {}
        for k, v in self.__mappings__.iteritems():
            if v.updateable:
                if hasattr(self, k):
                    arg = getattr(self, k)
                else:
                    arg = v.default
                    setattr(self, k, arg)
                kw[k] = arg
        pk = self.__primary_key__.name
        update_kw(self.__table__, '%s=?'%pk, getattr(self, pk), **kw)
        return self

    def delete(self):
        pk = self.__primary_key__.name
        args = getattr(self, pk)
        _update('delete from {0} where {1}=?'.format(self.__table__, pk), args)
        return self

    def insert(self):
        params = {}
        for k, v in self.__mappings__.iteritems():
            if k.insertable:
                if not hasattr(self, k):
                    setattr(self, k, v.default)
                params[v.name] = getattr(self, k)
        insert(self.__table__, **params)
        return self
