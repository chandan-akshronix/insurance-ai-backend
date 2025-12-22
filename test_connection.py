from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variable or use the direct connection string
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://dbadmin:admin%40123@insurance-ai-postgres-dev.postgres.database.azure.com:5432/postgres?sslmode=require')

def test_connection():
    try:
        print(f"Attempting to connect to: {DATABASE_URL}")
        
        # Create engine with SSL required
        engine = create_engine(DATABASE_URL)
        
        # Try to connect and execute a simple query
        with engine.connect() as connection:
            # Get database version
            result = connection.execute(text('SELECT version();'))
            version = result.fetchone()[0]
            
            # Get current database name
            result = connection.execute(text('SELECT current_database();'))
            db_name = result.fetchone()[0]
            
            print("\n✅ Successfully connected to PostgreSQL!")
            print(f"Database version: {version}")
            print(f"Current database: {db_name}")
            print(f"Server: insurance-ai-postgres-dev.postgres.database.azure.com")
            
            # Test if we can create a table
            connection.execute(text('''
                CREATE TABLE IF NOT EXISTS connection_test (
                    id SERIAL PRIMARY KEY,
                    test_column VARCHAR(50)
                );
            '''))
            print("\n✅ Successfully created test table!")
            
            # Insert a row
            connection.execute(text(
                "INSERT INTO connection_test (test_column) VALUES ('test_value')"
            ))
            connection.commit()
            print("✅ Successfully inserted test data!")
            
            # Query the data
            result = connection.execute(text("SELECT * FROM connection_test"))
            rows = result.fetchall()
            print("✅ Successfully queried test data!")
            print("\nData in connection_test table:")
            for row in rows:
                print(f"ID: {row[0]}, Value: {row[1]}")
            
            print("\n✅ Table 'connection_test' is kept for manual verification.")
            print("To check in psql, use: SELECT * FROM connection_test;")
            
    except Exception as e:
        print("\n❌ Connection test failed!")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("Testing PostgreSQL connection...\n")
    test_connection()