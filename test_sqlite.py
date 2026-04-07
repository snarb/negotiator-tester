import sqlite3
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()
db_path = os.getenv("NEGOTIATOR_DB_PATH", r"C:\repos\negotiator\negotiator.db")
print("Target DB path:", db_path)

db_path_fwd = db_path.replace('\\', '/')
db_uri = f"file:{urllib.parse.quote(db_path_fwd)}?mode=ro"
print("DB URI:", db_uri)

print("Connecting...")
try:
    conn = sqlite3.connect(db_uri, uri=True)
    print("Connected.")
    conn.close()
    print("Closed.")
except Exception as e:
    print("Error:", e)
