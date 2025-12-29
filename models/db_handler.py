import sqlite3
from datetime import datetime

class DatabaseHandler:

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
        
    def get_scrape_full_details(self, rowid):
        """Recupera o conteúdo completo para processar a extração inteligente."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT engine, termo, ano, pagina, html_source 
            FROM paginas_busca 
            WHERE rowid = ?
        """, (rowid,))
        return cursor.fetchone()

    def __init__(self, db_name="database.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """
        Cria as tabelas necessárias para o sistema, garantindo a existência de todas as 
        colunas para metadados institucionais (Sigla, Universidade, Programa e PDF).
        """
        cursor = self.conn.cursor()
        
        # 1. Tabela para os Scraps brutos (Histórico/Guia 2)
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
        
        # 2. Tabela consolidada para Pesquisas (Guia 3)
        # Inclui suporte para as Guias 4 (html_buscador) e 5 (html_repositorio)
        # Inclui as colunas finais de extração refinada
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pesquisas_extraidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                autor TEXT,
                link_buscador TEXT,
                link_repositorio TEXT,
                html_buscador TEXT,    -- Conteúdo HTML da BDTD (Guia 4)
                html_repositorio TEXT, -- Conteúdo HTML da Instituição (Guia 5)
                sigla_univ TEXT,       -- Sigla da IES
                nome_univ TEXT,        -- Nome da Universidade
                programa TEXT,         -- Programa de Pós-Graduação
                link_pdf TEXT,         -- Link direto para o arquivo PDF
                parent_rowid INTEGER
            )
        """)
        
        # 3. Tabela de Logs do Sistema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)        
        
        self.conn.execute('''CREATE TABLE IF NOT EXISTS dominios_filtros 
                             (dominio TEXT PRIMARY KEY, ativo INTEGER)''')
        self.conn.commit()

    def update_html_repositorio(self, rowid_pesquisa, html):
        """Salva o HTML capturado do link direto do repositório (Conteúdo da Guia 5)."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE pesquisas_extraidas SET html_repositorio = ? WHERE id = ?", (html, rowid_pesquisa))
        self.conn.commit()

    def get_html_repositorio(self, rowid_pesquisa):
        """
        Recupera o HTML do repositório (Guia 5) para que os Parsers específicos 
        possam realizar a extração refinada.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT html_repositorio FROM pesquisas_extraidas WHERE id = ?", (rowid_pesquisa,))
        res = cursor.fetchone()
        return res[0] if res else ""
    
    def insert_scrape(self, engine, termo, ano, pagina, html_source, link_busca):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO paginas_busca (engine, termo, ano, pagina, html_source, link_busca, data_coleta) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (engine, termo, str(ano), pagina, html_source, link_busca, datetime.now()))
        self.conn.commit()

    def insert_extracted_data(self, data_list):
        """Insere os dados iniciais extraídos (Título, Autor e Links)."""
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
        """Retorna exatamente as 8 colunas para a View."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT titulo, autor, link_buscador, link_repositorio, 
                   sigla_univ, nome_univ, programa, link_pdf 
            FROM pesquisas_extraidas ORDER BY id DESC
        """)
        return cursor.fetchall()

    def update_html_buscador(self, rowid_pesquisa, html):
        """Atualiza o registro com o HTML da Guia 4."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE pesquisas_extraidas SET html_buscador = ? WHERE id = ?", (html, rowid_pesquisa))
        self.conn.commit()

    def get_html_buscador(self, rowid_pesquisa):
        """Recupera o HTML para a Guia 4."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT html_buscador FROM pesquisas_extraidas WHERE id = ?", (rowid_pesquisa,))
        res = cursor.fetchone()
        return res[0] if res and res[0] else None

    def update_univ_data(self, res_id, sigla, nome):
        """Atualiza a sigla e o nome da universidade no banco de dados."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE pesquisas_extraidas 
            SET sigla_univ = ?, nome_univ = ? 
            WHERE id = ?
        """, (sigla, nome, res_id))
        self.conn.commit()

    def update_parser_data(self, res_id, data):
        """Salva o dicionário do Parser garantindo a gravação da sigla."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE pesquisas_extraidas 
            SET sigla_univ = ?, nome_univ = ?, programa = ?, link_pdf = ?
            WHERE id = ?
        """, (
            data.get('sigla', '-'), 
            data.get('universidade', '-'), 
            data.get('programa', '-'), 
            data.get('link_pdf', '-'), 
            res_id
        ))
        self.conn.commit()

    def get_link_by_id(self, res_id):
        """Retorna o link_buscador associado ao ID da pesquisa."""
        cursor = self.conn.execute("SELECT link_buscador FROM pesquisas_extraidas WHERE id=?", (res_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_all_repository_links(self):
        """Retorna todos os links de repositório para gerar a lista de raízes."""
        cursor = self.conn.execute("SELECT link_repositorio FROM pesquisas_extraidas")
        return [row[0] for row in cursor.fetchall()]

    def save_domain_state(self, domain, is_active):
        """Salva ou atualiza o estado de um domínio (1=marcado, 0=desmarcado)."""
        status = 1 if is_active else 0
        self.conn.execute("INSERT OR REPLACE INTO dominios_filtros (dominio, ativo) VALUES (?, ?)", 
                         (domain, status))
        self.conn.commit()

    def get_domain_states(self):
        """Retorna dicionário mapeando domínio ao seu estado booleano salvo."""
        cursor = self.conn.execute("SELECT dominio, ativo FROM dominios_filtros")
        return {row[0]: bool(row[1]) for row in cursor.fetchall()}
