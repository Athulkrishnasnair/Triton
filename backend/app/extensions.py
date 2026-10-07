from flask_sqlalchemy import SQLAlchemy
import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Creating SQLAlchemy obj
db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(connection, _connection_record):
    """SQLite leaves foreign-key enforcement off unless every connection opts in."""
    if isinstance(connection, sqlite3.Connection):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
