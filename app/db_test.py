import psycopg2
import os
from dotenv import load_dotenv

# 1. Load environment variables from .env
load_dotenv()

# 2. Read DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

print("Connecting to database...")

# 3. Create a connection to Postgres
conn = psycopg2.connect(DATABASE_URL)

print("Connection successful!")

# 4. Create a cursor (this lets us run SQL)
cur = conn.cursor()

# 5. Run a VERY simple query
cur.execute("SELECT 1;")

# 6. Fetch the result
result = cur.fetchone()

print("Query result:", result)

# 7. Clean up
cur.close()
conn.close()
