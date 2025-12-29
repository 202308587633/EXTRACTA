import sqlite3
import os

# Nome do arquivo de banco de dados (ajuste se o seu arquivo tiver outro nome)
DB_NAME = "database.db"

def limpar_tabela_pesquisas():
    # 1. Verifica se o banco de dados existe
    if not os.path.exists(DB_NAME):
        print(f"Erro: O arquivo '{DB_NAME}' não foi encontrado no diretório atual.")
        return

    try:
        # 2. Conecta ao banco de dados
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 3. Executa o comando para apagar os dados
        # O comando DELETE FROM sem WHERE remove todos os registros
        print(f"Limpando a tabela 'pesquisas_extraidas'...")
        cursor.execute("DELETE FROM pesquisas_extraidas")
        
        # Opcional: Reiniciar o contador de ID (autoincrement)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='pesquisas_extraidas'")

        # 4. Salva as alterações
        conn.commit()
        
        # 5. Verifica quantos registros restaram (deve ser 0)
        cursor.execute("SELECT COUNT(*) FROM pesquisas_extraidas")
        total = cursor.fetchone()[0]

        print(f"Sucesso! Tabela limpa. Total de registros atuais: {total}")

    except sqlite3.Error as e:
        print(f"Ocorreu um erro ao acessar o SQLite: {e}")
    
    finally:
        # 6. Fecha a conexão
        if conn:
            conn.close()

if __name__ == "__main__":
    confirmacao = input("Tem certeza que deseja apagar TODAS as pesquisas extraídas? (s/n): ")
    if confirmacao.lower() == 's':
        limpar_tabela_pesquisas()
    else:
        print("Operação cancelada.")