import sqlite3
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_name="database.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paginas_busca (
                engine TEXT,
                termo TEXT,
                ano TEXT,
                pagina INTEGER,
                html_source TEXT,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (engine, termo, ano, pagina)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()

    def insert_scrape(self, engine, termo, ano, pagina, html_source):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO paginas_busca (engine, termo, ano, pagina, html_source, data_coleta) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (engine, termo, str(ano), pagina, html_source, datetime.now()))
        self.conn.commit()

    def delete_scrape(self, rowid):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM paginas_busca WHERE rowid = ?", (rowid,))
        self.conn.commit()

    def get_scrape_content_by_id(self, rowid):
        """Busca apenas o HTML de um registro específico."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT html_source FROM paginas_busca WHERE rowid = ?", (rowid,))
        result = cursor.fetchone()
        return result[0] if result else None

    def log_event(self, message):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO system_logs (message, created_at) VALUES (?, ?)", 
                          (message, datetime.now()))
            self.conn.commit()
        except Exception as e:
            print(f"Erro ao salvar log: {e}")

    def fetch_all_logs(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT created_at, message FROM system_logs ORDER BY created_at DESC")
        return cursor.fetchall()

    def get_last_log_message(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT message FROM system_logs ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else "Pronto para iniciar."

    def fetch_all(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT rowid, termo, data_coleta, html_source 
            FROM paginas_busca 
            ORDER BY data_coleta DESC
        """)
        return cursor.fetchall()

    def close(self):
        self.conn.close()