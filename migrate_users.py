import json
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        dbname="cogi_db",
        user="mac",  # ou ton autre user PostgreSQL
        password="",
        host="localhost"
    )

with open('users.json') as f:
    users = json.load(f)

conn = get_db_connection()
cur = conn.cursor()

for email, data in users.items():
    cur.execute("""
        INSERT INTO users (email, password, first_name, last_name)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    """, (email, data['password'], data.get('first_name'), data.get('last_name')))

conn.commit()
cur.close()
conn.close()
print("✅ Migration terminée.")
