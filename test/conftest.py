"""Pytest configuration for setting up and tearing down the test database."""
import pytest
from django.db import connections
from django.core.management import call_command
from django.conf import settings

import psycopg2
from psycopg2 import sql as psql


def _admin_conn_kwargs():
    """Build connection kwargs for the administrative DB (usually 'postgres')

    Reads user/password/host/port from Django settings.DATABASES['default'] and
    sets the database name to 'postgres' so we can run CREATE/DROP DATABASE.
    """
    db = settings.DATABASES.get('default', {})
    engine = db.get('ENGINE', '')
    # Only support PostgreSQL here since we use CREATE/DROP DATABASE
    if 'postgres' not in engine and 'psycopg2' not in engine:
        raise RuntimeError('run_sql only supports PostgreSQL backends')

    kwargs = {
        'dbname': 'postgres'
    }
    if db.get('USER'):
        kwargs['user'] = db['USER']
    if db.get('PASSWORD'):
        kwargs['password'] = db['PASSWORD']
    if db.get('HOST'):
        kwargs['host'] = db['HOST']
    if db.get('PORT'):
        kwargs['port'] = db['PORT']

    print(kwargs)

    return kwargs


def run_sql(sql_statement):
    """Execute a SQL statement against the admin DB using Django settings.

    Example: run_sql("DROP DATABASE IF EXISTS my_test_db")
    Accepts either a string or a psycopg2.sql.Composed object.
    """
    kwargs = _admin_conn_kwargs()
    conn = psycopg2.connect(**kwargs)
    try:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(sql_statement)
    finally:
        conn.close()


def terminate_db_connections(dbname):
    """Terminate all other connections to `dbname` (except our own)."""
    kwargs = _admin_conn_kwargs()
    conn = psycopg2.connect(**kwargs)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                psql.SQL(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = {db} AND pid <> pg_backend_pid()"
                ).format(db=psql.Literal(dbname))
            )
    finally:
        conn.close()


@pytest.fixture(scope='module', autouse=True)
#@pytest.mark.django_db
def django_db_setup():
    """Set up a clean test database before any tests run."""

    settings.DATABASES['default']['NAME'] = settings.DATABASES['default'].get('NAME', 'p7_test')
    test_db_name = settings.DATABASES['default']['NAME']

    terminate_db_connections(test_db_name)
    run_sql(psql.SQL("DROP DATABASE IF EXISTS {}").format(psql.Identifier(test_db_name)))
    # pristine empty DB
    run_sql(psql.SQL("CREATE DATABASE {} TEMPLATE template0").format(psql.Identifier(test_db_name)))

    # create pg_trgm extension in the newly created test database
    kwargs = _admin_conn_kwargs()
    kwargs['dbname'] = test_db_name
    conn = psycopg2.connect(**kwargs)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    finally:
        conn.close()
    for connection in connections.all():
        connection.close()

    # Build schema (no business data)
    call_command('migrate', database='default', interactive=False, verbosity=0)
