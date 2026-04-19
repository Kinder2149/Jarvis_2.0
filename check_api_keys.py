import sqlite3

conn = sqlite3.connect("backend/data/jarvis.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT key, value FROM app_config WHERE category = 'api_keys'")
rows = cursor.fetchall()

print("=== Clés API dans la base de données ===")
for row in rows:
    key_name = row["key"]
    value = row["value"] or ""
    masked = f"...{value[-4:]}" if len(value) > 4 else value
    print(f"{key_name}: longueur={len(value)}, preview={masked}")

conn.close()
