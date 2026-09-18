import sqlite3
import os

db_path = os.path.join("backend", "campus.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Tables ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(table[0])

print("\n--- Parking Records Schema ---")
cursor.execute("PRAGMA table_info(parking_records);")
schema = cursor.fetchall()
for column in schema:
    print(column)

print("\n--- Recent Parking Records ---")
cursor.execute("SELECT * FROM parking_records ORDER BY id DESC LIMIT 5;")
records = cursor.fetchall()
for record in records:
    print(record)

conn.close()
