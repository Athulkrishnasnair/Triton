"""Small, non-destructive additive upgrades for the existing SQLite schema.

SQLAlchemy create_all() creates missing tables but does not add new columns to
existing tables. These columns are added in place. Legacy records with unknown
provenance default to UNKNOWN; the explicit seed marks its fixture rows DEMO.
No tables or records are removed.
"""

from sqlalchemy import inspect, text

from app.extensions import db


ADDITIVE_COLUMNS = {
    "auction": {
        "source": "VARCHAR(40) NOT NULL DEFAULT 'UNKNOWN'",
        "confidence": "FLOAT NOT NULL DEFAULT 0.0",
        "recorded_at": "DATETIME",
    },
    "announcement": {
        "source": "VARCHAR(40) NOT NULL DEFAULT 'UNKNOWN'",
    },
    "harbour_alert": {
        "source": "VARCHAR(40) NOT NULL DEFAULT 'UNKNOWN'",
    },
}


def ensure_provenance_columns():
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    for table_name, columns in ADDITIVE_COLUMNS.items():
        if table_name not in existing_tables:
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name, ddl in columns.items():
            if column_name in existing_columns:
                continue
            if column_name == "recorded_at" and db.engine.dialect.name == "postgresql":
                ddl = "TIMESTAMP"
            # Names/DDL come only from this fixed mapping, never user input.
            db.session.execute(text(
                f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {ddl}'
            ))
            if table_name == "auction" and column_name == "recorded_at":
                db.session.execute(text(
                    "UPDATE auction SET recorded_at = created_at WHERE recorded_at IS NULL"
                ))
            db.session.commit()
            existing_columns.add(column_name)
