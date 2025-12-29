import sqlite3
import os

# Nomes dos arquivos de banco de dados
SOURCE_DB = "resultados_scraper.db"
DEST_DB = "database.db"

def migrate_data():
    # 1. Verificar se os arquivos existem
    if not os.path.exists(SOURCE_DB):
        print(f"ERRO: O banco de origem '{SOURCE_DB}' não foi encontrado.")
        return

    print(f"--- Iniciando Migração ---")
    print(f"Origem: {SOURCE_DB}")
    print(f"Destino: {DEST_DB}")

    try:
        # 2. Conectar ao Banco de Origem (resultados_scraper.db)
        conn_src = sqlite3.connect(SOURCE_DB)
        cursor_src = conn_src.cursor()

        # Verificar se a tabela existe na origem
        try:
            cursor_src.execute("SELECT count(*) FROM paginas_busca")
            total_registros = cursor_src.fetchone()[0]
            print(f"Registros encontrados na origem: {total_registros}")
        except sqlite3.OperationalError:
            print("ERRO: A tabela 'paginas_busca' não existe no banco de origem.")
            return

        # Ler todos os dados da origem
        cursor_src.execute("SELECT engine, termo, ano, pagina, html_source, data_coleta FROM paginas_busca")
        rows = cursor_src.fetchall()

        # 3. Conectar ao Banco de Destino (database.db)
        conn_dest = sqlite3.connect(DEST_DB)
        cursor_dest = conn_dest.cursor()

        # 4. Criar a tabela 'paginas_busca' no destino (Cópia da estrutura original)
        # Mantivemos a estrutura exata do seu arquivo database-aplicativo.py
        print("Criando tabela 'paginas_busca' no destino...")
        cursor_dest.execute('''
            CREATE TABLE IF NOT EXISTS paginas_busca (
                engine TEXT,
                termo TEXT,
                ano TEXT,
                pagina INTEGER,
                html_source TEXT,
                data_coleta TIMESTAMP,
                PRIMARY KEY (engine, termo, ano, pagina)
            )
        ''')

        # 5. Inserir os dados no destino
        print("Transferindo dados...")
        inserted_count = 0
        skipped_count = 0

        query_insert = '''
            INSERT OR IGNORE INTO paginas_busca (engine, termo, ano, pagina, html_source, data_coleta)
            VALUES (?, ?, ?, ?, ?, ?)
        '''

        for row in rows:
            cursor_dest.execute(query_insert, row)
            if cursor_dest.rowcount > 0:
                inserted_count += 1
            else:
                skipped_count += 1 # Ignorado pois já existia (devido à Primary Key)

        conn_dest.commit()

        # 6. Finalização
        print("-" * 30)
        print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"Registros transferidos: {inserted_count}")
        print(f"Registros ignorados (já existiam): {skipped_count}")
        print(f"Total na tabela de destino: {inserted_count + skipped_count}")

    except sqlite3.Error as e:
        print(f"Ocorreu um erro no banco de dados: {e}")
    finally:
        if 'conn_src' in locals(): conn_src.close()
        if 'conn_dest' in locals(): conn_dest.close()

if __name__ == "__main__":
    migrate_data()