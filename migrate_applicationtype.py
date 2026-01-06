
import os
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Fetching all application_process records...")
        res = conn.execute(text('SELECT id, "agentData" FROM application_process'))
        rows = res.fetchall()
        
        updated_count = 0
        for row in rows:
            rid = row[0]
            agent_data = row[1] or {}
            if isinstance(agent_data, str):
                try:
                    agent_data = json.loads(agent_data)
                except:
                    agent_data = {}
            
            # Determine type
            app_type = 'policy'
            if any(k in agent_data for k in ["claim_id", "fnol_data", "policy_sql_data"]):
                app_type = 'claim'
            
            # Update
            conn.execute(
                text('UPDATE application_process SET applicationtype = :t WHERE id = :id'),
                {"t": app_type, "id": rid}
            )
            updated_count += 1
        
        conn.commit()
        print(f"Successfully updated {updated_count} records.")

if __name__ == "__main__":
    migrate()
