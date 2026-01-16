
from database import engine
from sqlalchemy import inspect

def check_schema():
    try:
        insp = inspect(engine)
        columns = insp.get_columns('payments')
        print("Columns in 'payments' table:")
        for col in columns:
            print(f"- {col['name']} (Nullable: {col['nullable']})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
