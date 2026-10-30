from sqlalchemy import create_engine, text

SCHEMA = [
    "CREATE TABLE IF NOT EXISTS users (id VARCHAR(64) PRIMARY KEY, email VARCHAR(200) UNIQUE NOT NULL, password_hash TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS items (id VARCHAR(64) PRIMARY KEY, owner VARCHAR(64) NOT NULL REFERENCES users(id), name VARCHAR(100) NOT NULL, description TEXT NOT NULL, price DOUBLE PRECISION NOT NULL)",
    "CREATE TABLE IF NOT EXISTS categories (id VARCHAR(64) PRIMARY KEY, owner VARCHAR(64) NOT NULL REFERENCES users(id), name VARCHAR(100) NOT NULL)",
    "CREATE TABLE IF NOT EXISTS devices (id VARCHAR(64) PRIMARY KEY, owner VARCHAR(64) NOT NULL REFERENCES users(id), name VARCHAR(100) NOT NULL, key_hash VARCHAR(64) NOT NULL, raw INTEGER, touched INTEGER, led INTEGER, seen DOUBLE PRECISION)",
    "CREATE TABLE IF NOT EXISTS commands (id VARCHAR(64) PRIMARY KEY, device VARCHAR(64) NOT NULL REFERENCES devices(id), led INTEGER NOT NULL, state VARCHAR(20) NOT NULL, created DOUBLE PRECISION NOT NULL, acknowledged DOUBLE PRECISION)",
]

class Database:
    def __init__(self, url):
        is_postgres = url.startswith("postgresql")
        args = {"check_same_thread": False} if url.startswith("sqlite") else {"options": "-c search_path=learning27"} if is_postgres else {}
        self.engine = create_engine(url, connect_args=args, pool_pre_ping=True)
        with self.engine.begin() as con:
            if is_postgres:
                con.execute(text("CREATE SCHEMA IF NOT EXISTS learning27"))
            for sql in SCHEMA:
                con.execute(text(sql))

    def one(self, sql, **params):
        with self.engine.connect() as con:
            row = con.execute(text(sql), params).mappings().first()
            return dict(row) if row else None

    def all(self, sql, **params):
        with self.engine.connect() as con:
            return [dict(r) for r in con.execute(text(sql), params).mappings()]

    def execute(self, sql, **params):
        with self.engine.begin() as con:
            return con.execute(text(sql), params).rowcount
