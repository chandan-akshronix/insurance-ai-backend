
import os
import psycopg2
from urllib.parse import urlparse

# DATABASE CONNECTION URL
# Update this if your .env or actual connection string is different
DATABASE_URL = "postgresql://dbadmin:admin%40123@insurance-ai-postgres-dev.postgres.database.azure.com:5432/postgres?sslmode=require"

def fix_payment_schema():
    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 1. Alter policyId to be NULLABLE
        print("Altering policyId to be nullable...")
        try:
            cur.execute("ALTER TABLE payments ALTER COLUMN \"policyId\" DROP NOT NULL;")
        except Exception as e:
            print(f"Warning altering policyId: {e}")
            conn.rollback()
        else:
            print("Success.")
            conn.commit()

        # 2. Add policyNumber column
        print("Adding policyNumber column...")
        try:
            cur.execute("ALTER TABLE payments ADD COLUMN \"policyNumber\" VARCHAR;")
        except Exception as e:
            print(f"Warning adding policyNumber: {e}")
            conn.rollback()
        else:
            print("Success.")
            conn.commit()

        # 3. Add applicationId column
        print("Adding applicationId column...")
        try:
            cur.execute("ALTER TABLE payments ADD COLUMN \"applicationId\" VARCHAR;")
        except Exception as e:
            print(f"Warning adding applicationId: {e}")
            conn.rollback()
        else:
            print("Success.")
            conn.commit()

        cur.close()
        conn.close()
        print("\nMigration completed successfully.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    fix_payment_schema()
