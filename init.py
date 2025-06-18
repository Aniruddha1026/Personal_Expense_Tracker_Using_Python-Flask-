import sqlite3

conn=sqlite3.connect("expense_tracker.db")

cursor=conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS signup(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
    )
""")

cursor.execute("""
               CREATE TABLE IF NOT EXISTS expense(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               username TEXT NOT NULL,
               title TEXT NOT NULL,
               amount REAL NOT NULL,
               date TEXT NOT NULL,
               FOREIGN KEY (username) REFERENCES signup(username))
               """)
conn.commit()
conn.close()
print("database initialized successfully")
