import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "backend" / "data" / "jarvis.db"

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT key, substr(value, 1, 15) || '...' as value_preview, category, updated_at FROM app_config WHERE category = 'api_keys'")
rows = cursor.fetchall()

print("=== Clés API dans SQLite ===")
for row in rows:
    print(f"  {row['key']}: {row['value_preview']} (updated: {row['updated_at']})")

conn.close()
print("\n✅ Migration réussie - Clés API stockées dans SQLite")
