import sqlite3

conn = sqlite3.connect('backend/data/jarvis.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

row = cursor.execute(
    "SELECT output_data FROM pipeline_steps WHERE session_id = 9 AND step_name = 'generation_index'"
).fetchone()

if row:
    output = row['output_data']
    print("=== PREVIEW (first 1000 chars) ===")
    print(output[:1000])
    print("\n=== LENGTH ===")
    print(f"Total length: {len(output)} chars")
else:
    print("No data found")

conn.close()
