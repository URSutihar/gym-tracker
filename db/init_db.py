import sqlite3
import os

DB_PATH = os.environ.get(
    'GYM_LOG_DB_PATH',
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'gym_log.db'),
)
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')

def initialize_database():
    print(f"Initializing database at {DB_PATH}")
    
    if not os.path.exists(SCHEMA_PATH):
        print(f"Error: Schema file not found at {SCHEMA_PATH}")
        return
        
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.executescript(schema_sql)
        conn.commit()
        print("Database schema successfully created/updated.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    initialize_database()
