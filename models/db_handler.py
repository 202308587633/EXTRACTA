import sqlite3
from datetime import datetime

class DatabaseHandler:
        
    def __init__(self, db_name="database.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def insert_scrape(self, engine, termo, ano, pagina, html_source, link_busca):
        cursor = self.conn.cursor()
        # Inserção incluindo o novo campo link_busca
        cursor.execute("""
            INSERT OR REPLACE INTO paginas_busca (engine, termo, ano, pagina, html_source, link_busca, data_coleta) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (engine, termo, str(ano), pagina, html_source, link_busca, datetime.now()))
        self.conn.commit()

    def delete_scrape(self, rowid):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM paginas_busca WHERE rowid = ?", (rowid,))
        self.conn.commit()

    def get_scrape_content_by_id(self, rowid):
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

    def close(self):
        self.conn.close()

    def create_tables(self):
        """Cria as tabelas necessárias, incluindo a nova estrutura para pesquisas extraídas."""
        cursor = self.conn.cursor()
        
        # Tabela para os Scraps brutos (Histórico)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paginas_busca (
                engine TEXT,
                termo TEXT,
                ano TEXT,
                pagina INTEGER,
                html_source TEXT,
                link_busca TEXT,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (engine, termo, ano, pagina)
            )
        """)
        
        # Tabela para as Pesquisas Extraídas (Dados solicitados)
        # Inclui os dois tipos de links: link_buscador e link_repositorio
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pesquisas_extraidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                autor TEXT,
                link_buscador TEXT,
                link_repositorio TEXT,
                parent_rowid INTEGER
            )
        """)
        
        # Tabela de Logs do Sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()

    def insert_extracted_data(self, data_list):
        """Insere os dados refinados extraídos do HTML."""
        cursor = self.conn.cursor()
        cursor.executemany("""
            INSERT INTO pesquisas_extraidas (titulo, autor, link_buscador, link_repositorio, parent_rowid)
            VALUES (?, ?, ?, ?, ?)
        """, data_list)
        self.conn.commit()

    def fetch_all(self):
        """Retorna o histórico de capturas para a aba 'Histórico'."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT rowid, termo, data_coleta, html_source, pagina 
            FROM paginas_busca 
            ORDER BY data_coleta DESC
        """)
        return cursor.fetchall()

    def fetch_extracted_data(self):
        """Busca os dados para preencher a tabela na aba 'Pesquisas'."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT titulo, autor, link_buscador, link_repositorio 
            FROM pesquisas_extraidas 
            ORDER BY id DESC
        """)
        return cursor.fetchall()

    def get_scrape_full_details(self, rowid):
        """Recupera o conteúdo completo para processar a extração inteligente."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT engine, termo, ano, pagina, html_source 
            FROM paginas_busca 
            WHERE rowid = ?
        """, (rowid,))
        return cursor.fetchone()
    
