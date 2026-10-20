"""Acesso ao PostgreSQL (psycopg2 + pool de conexões).

query()   -> SELECT, devolve lista de dicts (ou um dict com one=True)
execute() -> INSERT/UPDATE/DELETE; com RETURNING devolve a linha
tx()      -> várias instruções na mesma transação
"""
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import psycopg2.pool

import config

psycopg2.extras.register_uuid()

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(1, 10, config.DATABASE_URL)
    return _pool


@contextmanager
def tx():
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def query(sql, params=None, one=False):
    with tx() as cur:
        cur.execute(sql, params or ())
        rows = cur.fetchall()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=None):
    with tx() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone() if cur.description else None
