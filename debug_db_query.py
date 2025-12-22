r"""Simple script to query the same database engine used by the FastAPI app.

Run this from the project root while your virtualenv is active to confirm which
rows exist in the `users` table according to SQLAlchemy's engine settings.

Example (PowerShell):
.venv\Scripts\activate ; python debug_db_query.py
"""
import sys
import traceback
from sqlalchemy import text
from database import engine


def mask(s: str) -> str:
    if not s:
        return ""
    try:
        return s[0] + "***" + s[-1]
    except Exception:
        return "***"


def main():
    try:
        url = engine.url
        print("Engine URL info:")
        print(f"  drivername: {url.drivername}")
        print(f"  host: {url.host}")
        print(f"  port: {url.port}")
        print(f"  database: {url.database}")
        print(f"  username (masked): {mask(url.username or '')}")

        with engine.connect() as conn:
            print('\nRunning SELECT on users table:')
            # Use text() to be compatible with SQLAlchemy 2.x
            # Avoid selecting camelCase column names directly (Postgres folds unquoted
            # identifiers to lowercase). Select common lowercase columns that should exist.
            result = conn.execute(text("SELECT id, email, phone FROM users ORDER BY id DESC LIMIT 10"))
            rows = result.fetchall()
            if not rows:
                print('No rows returned (users table empty or table not present).')
                return
            for r in rows:
                print(dict(r._mapping))

    except Exception as e:
        print("An error occurred while querying the DB:")
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
