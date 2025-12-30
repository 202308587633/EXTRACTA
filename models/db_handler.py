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
        """Grava logs com proteção para não quebrar caso a tabela ainda não exista."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO system_logs (message, created_at) VALUES (?, ?)", 
                          (message, datetime.now()))
            self.conn.commit()
        except sqlite3.OperationalError:
            # Fallback silencioso caso a tabela realmente não exista no momento da chamada
            print(f"Log (Console apenas): {message}")
        except Exception as e:
            print(f"Erro inesperado ao salvar log: {e}")

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
        """Recupera os detalhes completos incluindo a URL original para possibilitar a paginação."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT engine, termo, ano, pagina, html_source, link_busca 
            FROM paginas_busca 
            WHERE rowid = ?
        """, (rowid,))
        return cursor.fetchone()

    def __init__(self, db_name="database.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """Cria as tabelas necessárias garantindo que a tabela de logs exista primeiro."""
        cursor = self.conn.cursor()
        
        # 1. CRIAR TABELA DE LOGS PRIMEIRO
        # Isso permite que qualquer erro ou migração subsequente seja registrado no banco.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                message TEXT, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

        # 2. Tabela de Histórico (Guia 2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paginas_busca (
                engine TEXT, termo TEXT, ano TEXT, pagina INTEGER,
                html_source TEXT, link_busca TEXT, data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (engine, termo, ano, pagina)
            )
        """)
        
        # 3. Tabela consolidada para Pesquisas (Guia 3)
        # Iniciamos com a estrutura base para garantir a compatibilidade.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pesquisas_extraidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT, autor TEXT, link_buscador TEXT, link_repositorio TEXT,
                html_buscador TEXT, html_repositorio TEXT, sigla_univ TEXT,
                nome_univ TEXT, programa TEXT, link_pdf TEXT, parent_rowid INTEGER
            )
        """)

        # --- LÓGICA DE MIGRAÇÃO: Adiciona colunas se não existirem ---
        # Agora o self.log_event funcionará pois a tabela system_logs já foi criada no passo 1.
        cursor.execute("PRAGMA table_info(pesquisas_extraidas)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'termo_pesquisado' not in columns:
            cursor.execute("ALTER TABLE pesquisas_extraidas ADD COLUMN termo_pesquisado TEXT")
            self.log_event("Migração: Coluna 'termo_pesquisado' adicionada com sucesso.")
            
        if 'ano_pesquisado' not in columns:
            cursor.execute("ALTER TABLE pesquisas_extraidas ADD COLUMN ano_pesquisado TEXT")
            self.log_event("Migração: Coluna 'ano_pesquisado' adicionada com sucesso.")

        # 4. Filtros de Domínio (Guia 4)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS dominios_filtros 
                             (dominio TEXT PRIMARY KEY, ativo INTEGER)''')
        
        self.conn.commit()

    def update_html_repositorio(self, rowid_pesquisa, html):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE pesquisas_extraidas SET html_repositorio = ? WHERE id = ?", (html, rowid_pesquisa))
        self.conn.commit()

    def get_html_repositorio(self, rowid_pesquisa):
        cursor = self.conn.cursor()
        cursor.execute("SELECT html_repositorio FROM pesquisas_extraidas WHERE id = ?", (rowid_pesquisa,))
        res = cursor.fetchone()
        return res[0] if res else ""
    
    def insert_scrape(self, engine, termo, ano, pagina, html_source, link_busca):
        """Insere ou substitui um registro de busca. O 'termo' agora será o texto da Combobox."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO paginas_busca (engine, termo, ano, pagina, html_source, link_busca, data_coleta) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (engine, termo, str(ano), pagina, html_source, link_busca, datetime.now()))
        self.conn.commit()

    def insert_extracted_data(self, data_list):
        """Insere os dados extraídos vindo do Histórico para a aba de Pesquisas."""
        cursor = self.conn.cursor()
        cursor.executemany("""
            INSERT INTO pesquisas_extraidas 
            (titulo, autor, link_buscador, link_repositorio, parent_rowid, termo_pesquisado, ano_pesquisado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data_list)
        self.conn.commit()

    def fetch_all(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT rowid, termo, data_coleta, html_source, pagina 
            FROM paginas_busca 
            ORDER BY data_coleta DESC
        """)
        return cursor.fetchall()

    def fetch_extracted_data(self):
        """Retorna as 10 colunas para preencher a Treeview na Guia 3."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT titulo, autor, link_buscador, link_repositorio, 
                   sigla_univ, nome_univ, programa, link_pdf,
                   termo_pesquisado, ano_pesquisado 
            FROM pesquisas_extraidas 
            ORDER BY id DESC
        """)
        return cursor.fetchall()

    def update_html_buscador(self, rowid_pesquisa, html):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE pesquisas_extraidas SET html_buscador = ? WHERE id = ?", (html, rowid_pesquisa))
        self.conn.commit()

    def get_html_buscador(self, rowid_pesquisa):
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
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE pesquisas_extraidas 
            SET sigla_univ = ?, nome_univ = ?, programa = ?, link_pdf = ?
            WHERE id = ?
        """, (data.get('sigla', '-'), data.get('universidade', '-'), 
              data.get('programa', '-'), data.get('link_pdf', '-'), res_id))
        self.conn.commit()

    def get_link_by_id(self, res_id):
        cursor = self.conn.execute("SELECT link_buscador FROM pesquisas_extraidas WHERE id=?", (res_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_all_repository_links(self):
        """Busca links únicos para gerar a lista alfabética de domínios."""
        cursor = self.conn.execute("""
            SELECT DISTINCT link_repositorio 
            FROM pesquisas_extraidas 
            WHERE link_repositorio IS NOT NULL AND link_repositorio != '-'
        """)
        return [row[0] for row in cursor.fetchall()]

    def save_domain_state(self, domain, is_active):
        """Salva a escolha do usuário (marcado/desmarcado) sobre um domínio."""
        status = 1 if is_active else 0
        self.conn.execute("""
            INSERT OR REPLACE INTO dominios_filtros (dominio, ativo) 
            VALUES (?, ?)
        """, (domain, status))
        self.conn.commit()

    def get_domain_states(self):
        """Recupera os estados salvos para renderizar os checkboxes."""
        cursor = self.conn.execute("SELECT dominio, ativo FROM dominios_filtros")
        return {row[0]: bool(row[1]) for row in cursor.fetchall()}

    def fetch_research_record(self, res_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT titulo, autor, link_buscador, link_repositorio, 
                   sigla_univ, nome_univ, programa, link_pdf,
                   termo_pesquisado, ano_pesquisado 
            FROM pesquisas_extraidas 
            WHERE id = ?
        """, (res_id,))
        return cursor.fetchone()

    def get_all_research_ids(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM pesquisas_extraidas ORDER BY id DESC")
        return [row[0] for row in cursor.fetchall()]

    def get_all_research_data(self):
        return self.fetch_extracted_data()

    def save_html_buscador(self, rowid, html):
        self.update_html_buscador(rowid, html)

    def save_html_repositorio(self, rowid, html):
        self.update_html_repositorio(rowid, html)

    def update_research_extracted_data(self, res_id, sigla, univ, prog, pdf):
        cursor = self.conn.cursor()
        updates = []
        params = []
        
        if sigla:
            updates.append("sigla_univ = ?")
            params.append(sigla)
        if univ:
            updates.append("nome_univ = ?")
            params.append(univ)
        if prog:
            updates.append("programa = ?")
            params.append(prog)
        if pdf:
            updates.append("link_pdf = ?")
            params.append(pdf)
            
        if not updates:
            return

        params.append(res_id)
        sql = f"UPDATE pesquisas_extraidas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(sql, tuple(params))
        self.conn.commit()

    def get_research_links_and_ids(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, link_repositorio 
            FROM pesquisas_extraidas 
            WHERE html_repositorio IS NULL OR html_repositorio = ''
            ORDER BY id DESC
        """)
        return cursor.fetchall()

    def get_ids_with_stored_html(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id FROM pesquisas_extraidas 
            WHERE (html_repositorio IS NOT NULL AND html_repositorio != '' AND html_repositorio != '-')
               OR (html_buscador IS NOT NULL AND html_buscador != '' AND html_buscador != '-')
        """)
        return [row[0] for row in cursor.fetchall()]

    def fetch_filtered_researches(self, filters):
        base_query = """
            SELECT id, titulo, autor, link_buscador, link_repositorio, 
                   sigla_univ, nome_univ, programa, link_pdf, 
                   termo_pesquisado, ano_pesquisado 
            FROM pesquisas_extraidas WHERE 1=1
        """
        params = []
        
        field_map = {
            'html_busc': 'html_buscador',
            'html_repo': 'html_repositorio',
            'sigla': 'sigla_univ',
            'univ': 'nome_univ',
            'prog': 'programa'
        }

        for key, value in filters.items():
            if value == 'Indiferente':
                continue
            
            col = field_map.get(key)
            if not col: continue

            if value == 'Sim':
                base_query += f" AND {col} IS NOT NULL AND {col} != '' AND {col} != '-'"
            elif value == 'Não':
                base_query += f" AND ({col} IS NULL OR {col} = '' OR {col} = '-')"

        cursor = self.conn.cursor()
        cursor.execute(base_query, params)
        return cursor.fetchall()
