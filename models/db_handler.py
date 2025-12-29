import sqlite3
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_name="database.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrapes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                html_content TEXT,
                created_at DATETIME
            )
        """)
        self.conn.commit()

    def insert_scrape(self, url, html_content):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO scrapes (url, html_content, created_at) VALUES (?, ?, ?)",
                       (url, html_content, datetime.now()))
        self.conn.commit()

    def close(self):
        self.conn.close()