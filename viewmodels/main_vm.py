import threading
import webbrowser
import tempfile
import os
import re  # Necessário para encontrar os padrões de página no HTML
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime
from html.parser import HTMLParser
from io import StringIO
from models.db_handler import DatabaseHandler
from models.web_scraper import WebScraper
from bs4 import BeautifulSoup
from services.parser_factory import ParserFactory # Certifique-se de que o caminho está correto

class MLStripper(HTMLParser):

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()
class MainViewModel:

    def __init__(self):
        self.db = DatabaseHandler()
        self.factory = ParserFactory() # Inicializa a fábrica de parsers

    def _update_step(self, message, callback):
        self.db.log_event(message)
        if callback:
            callback(message)

    def perform_scrape(self, url, termo_amigavel, ano_selecionado, on_status_change, on_error):
        """
        Realiza o scrap gravando o texto amigável da Combobox e o ano no histórico.
        """
        def task():
            try:
                self._update_step(f"Validando busca: {termo_amigavel}...", on_status_change)
                if not url.strip():
                    raise ValueError("A URL de destino não pode estar vazia.")

                engine = "BDTD" # Identificador fixo para o buscador principal

                self._update_step(f"Baixando conteúdo da BDTD ({ano_selecionado})...", on_status_change)
                
                scraper = WebScraper()
                html = scraper.download_page(url, on_progress=on_status_change)
                
                if not html:
                    raise Exception("Falha ao capturar o HTML da página inicial da BDTD.")

                self._update_step("Persistindo busca no histórico...", on_status_change)
                # Grava o termo amigável da Combobox em vez da URL longa
                self.db.insert_scrape(
                    engine=engine,
                    termo=termo_amigavel,
                    ano=str(ano_selecionado),
                    pagina=1,
                    html_source=html,
                    link_busca=url
                )
                self._update_step(f"Captura de '{termo_amigavel}' finalizada!", on_status_change)
            except Exception as e:
                erro_msg = str(e)
                self.db.log_event(f"ERRO NO SCRAPE: {erro_msg}")
                on_error(erro_msg)

        threading.Thread(target=task, daemon=True).start()

    def get_history(self):
        return self.db.fetch_all()

    def get_system_logs(self):
        return self.db.fetch_all_logs()

    def get_initial_status(self):
        return self.db.get_last_log_message()

    def render_html_to_text(self, html_content):
        try:
            s = MLStripper()
            s.feed(html_content)
            return s.get_data()
        except Exception:
            return html_content

    def process_pagination(self, rowid, on_status_change, callback_refresh):
        def task():
            try:
                record = self.db.get_scrape_full_details(rowid)
                if not record: return
                engine, termo_original, ano, pagina_inicial, html_source = record
                
                matches = re.findall(r'page=(\d+)', html_source)
                if not matches: return
                max_page = max(map(int, matches))

                parsed_url = urlparse(termo_original)
                query_params = parse_qs(parsed_url.query)
                scraper = WebScraper() # Instancia uma vez para o loop

                for p in range(2, max_page + 1):
                    self._update_step(f"Capturando página {p} de {max_page}...", on_status_change)
                    query_params['page'] = [str(p)]
                    new_query = urlencode(query_params, doseq=True)
                    new_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, 
                                          parsed_url.params, new_query, parsed_url.fragment))
                    
                    # CORREÇÃO: Usa download_page do scraper instanciado
                    new_html = scraper.download_page(new_url, on_progress=on_status_change)
                    if new_html:
                        self.db.insert_scrape(engine, termo_original, ano, p, new_html, new_url)
                    time.sleep(1)

                self._update_step(f"Ciclo finalizado.", on_status_change)
                if callback_refresh: callback_refresh()
            except Exception as e:
                self._update_step(f"Erro na paginação: {str(e)}", on_status_change)

        threading.Thread(target=task, daemon=True).start()

    def open_in_browser(self, rowid):
        """
        Recupera o HTML do banco, cria um arquivo temporário e abre no navegador padrão.
        """
        try:
            html_content = self.db.get_scrape_content_by_id(rowid)
            if not html_content:
                return

            # Cria um arquivo temporário com extensão .html
            fd, path = tempfile.mkstemp(suffix=".html")
            
            with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                tmp.write(html_content)
            
            # Abre o arquivo no navegador padrão do sistema
            webbrowser.open(f'file://{path}')
            
            self.db.log_event(f"HTML (ID {rowid}) aberto no navegador.")

        except Exception as e:
            self.db.log_event(f"Erro ao abrir navegador: {str(e)}")

    def _find_pattern(self, pattern, text):
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None
   
    def extract_research_data(self, rowid, on_status_change, on_error, callback_refresh):
        """
        Processa o histórico bruto para a tabela de pesquisas.
        Popula as 10 colunas, incluindo Termo e Ano originais da busca.
        """
        def task():
            try:
                self._update_step("Analisando estrutura do HTML...", on_status_change)
                record = self.db.get_scrape_full_details(rowid)
                if not record: return
                
                # record: (engine, termo_orig, ano_orig, pagina, html)
                termo_orig, ano_orig, html_content = record[1], record[2], record[4]
                soup = BeautifulSoup(html_content, 'html.parser')
                results = soup.select('.result.card-results')

                extracted_to_db = []
                for res in results:
                    title_tag = res.select_one('h2 a.title')
                    titulo = title_tag.get_text(strip=True) if title_tag else "-"
                    l_busc = title_tag['href'] if title_tag else "-"
                    if l_busc.startswith('/'): 
                        l_busc = "https://bdtd.ibict.br" + l_busc

                    autor = res.select_one('a[href*="/Author/"]').get_text(strip=True) if res.select_one('a[href*="/Author/"]') else "-"
                    repo_tag = res.find('a', string=lambda s: s and "Acessar documento" in s)
                    l_repo = repo_tag['href'] if repo_tag else "-"

                    # 7 valores: titulo, autor, link_busc, link_repo, rowid, termo, ano
                    extracted_to_db.append((titulo, autor, l_busc, l_repo, rowid, termo_orig, ano_orig))

                if extracted_to_db:
                    self.db.insert_extracted_data(extracted_to_db)
                    self._update_step(f"Sucesso: {len(extracted_to_db)} pesquisas extraídas.", on_status_change)
                
                if callback_refresh: callback_refresh()
            except Exception as e:
                self.db.log_event(f"Erro na extração inteligênte: {str(e)}")
                if on_error: on_error(str(e))

        threading.Thread(target=task, daemon=True).start()

    def get_research_results(self):
        """Retorna os resultados da tabela de pesquisas processando agora as 10 colunas."""
        return self.db.fetch_extracted_data()

    def scrape_buscador_link(self, pesquisa_id, url, on_status_change, callback_display):
        def task():
            try:
                self._update_step(f"Acessando buscador: {url[:40]}...", on_status_change)
                scraper = WebScraper()
                html = scraper.download_page(url, on_progress=on_status_change) # CORREÇÃO
                if html:
                    self.db.update_html_buscador(pesquisa_id, html)
                    self._update_step("HTML do buscador salvo!", on_status_change)
                    if callback_display: callback_display(html)
            except Exception as e:
                self._update_step(f"Erro: {str(e)}", on_status_change)
        threading.Thread(target=task, daemon=True).start()

    def fetch_saved_html_buscador(self, pesquisa_id):
        return self.db.get_html_buscador(pesquisa_id)

    def preview_html_in_browser(self, pesquisa_id):
        """Busca o HTML no banco e abre no navegador via arquivo temporário."""
        html_content = self.db.get_html_buscador(pesquisa_id)
        
        if not html_content:
            return False, "Nenhum HTML encontrado para esta pesquisa. Faça o Scrap primeiro."

        try:
            # Cria um arquivo temporário que não é deletado imediatamente
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                temp_path = f.name
            
            # Abre o arquivo no navegador padrão
            webbrowser.open(f"file://{os.path.realpath(temp_path)}")
            return True, "Abrindo no navegador..."
        except Exception as e:
            return False, f"Erro ao abrir navegador: {str(e)}"

    def scrape_repositorio_link(self, pesquisa_id, url, on_status_change, callback_display):
        def task():
            try:
                if not url or url == "-": return
                self._update_step(f"Acessando Repositório: {url[:40]}...", on_status_change)
                scraper = WebScraper()
                html = scraper.download_page(url, on_progress=on_status_change) # CORREÇÃO (Fallback automático p/ Selenium)
                if html:
                    self.db.update_html_repositorio(pesquisa_id, html)
                    self._update_step("HTML do repositório salvo!", on_status_change)
                    if callback_display: callback_display(html)
            except Exception as e:
                self._update_step(f"Erro no repositório: {str(e)}", on_status_change)
        threading.Thread(target=task, daemon=True).start()
        
    def preview_html_content_in_browser(self, html_content):
        """
        Recebe o conteúdo HTML bruto, salva em arquivo temporário e abre no navegador.
        """
        if not html_content:
            return False, "Nenhum conteúdo HTML disponível para exibir."

        try:
            # Cria um arquivo temporário que não é removido imediatamente para permitir a leitura pelo navegador
            fd, path = tempfile.mkstemp(suffix=".html")
            
            with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                tmp.write(html_content)
            
            # Abre o arquivo no navegador padrão do sistema
            webbrowser.open(f'file://{path}')
            
            self.db.log_event("HTML aberto no navegador para pré-visualização.")
            return True, "Abrindo navegador..."

        except Exception as e:
            msg_erro = f"Erro ao abrir navegador: {str(e)}"
            self.db.log_event(msg_erro)
            return False, msg_erro
        
    def extract_university_info(self, res_id, on_status_change, callback_refresh):
        """Extração inteligente com suporte a 8 colunas e Link do PDF."""
        def task():
            try:
                cursor = self.db.conn.cursor()
                cursor.execute("""
                    SELECT link_buscador, html_buscador, link_repositorio, html_repositorio 
                    FROM pesquisas_extraidas WHERE id=?
                """, (res_id,))
                row = cursor.fetchone()
                
                if not row: return

                l_busc, h_busc, l_repo, h_repo = row
                
                # Escolhe a melhor fonte disponível
                source_html = h_repo if h_repo else h_busc
                active_link = l_repo if h_repo else l_busc

                if not source_html:
                    self._update_step("Erro: Nenhum HTML capturado. Faça o Scrap primeiro.", on_status_change)
                    return

                self._update_step(f"Iniciando Parser para {active_link[:30]}...", on_status_change)
                parser = self.factory.get_parser(active_link, html_content=source_html)
                # Extrai dados (Sigla, Nome, Programa, PDF)
                details = parser.extract_pure_soup(source_html, active_link, on_progress=on_status_change)                
                
                # Salva no Banco (certifique-se que o db_handler tem a coluna link_pdf)
                self.db.update_parser_data(res_id, details)
                
                self._update_step(f"Sucesso: {details.get('sigla')} processada.", on_status_change)
                if callback_refresh: callback_refresh()

            except Exception as e:
                self.db.log_event(f"Erro na extração: {str(e)}")
                self._update_step(f"Erro: {str(e)}", on_status_change)

        threading.Thread(target=task, daemon=True).start()
       
    def preview_pdf_in_browser(self, res_id):
        """Busca o link do PDF no banco e abre no navegador."""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT link_pdf FROM pesquisas_extraidas WHERE id=?", (res_id,))
            row = cursor.fetchone()
            if row and row[0] and row[0] != "-":
                webbrowser.open(row[0])
                return True, "Abrindo PDF..."
            return False, "Link do PDF não disponível. Execute a extração (Parser) primeiro."
        except Exception as e:
            return False, str(e)
    
    def perform_repositorio_scrap(self, res_id, on_status_change, callback_refresh):
        """Usa o WebScraper com fallback automático para Selenium."""
        def task():
            try:
                # 1. Recupera o link do banco
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT link_repositorio FROM pesquisas_extraidas WHERE id=?", (res_id,))
                row = cursor.fetchone()
                
                if not row or row[0] == "-":
                    self._update_step("Erro: Link do repositório inválido.", on_status_change)
                    return

                url = row[0]
                
                # 2. Instancia o scraper e chama o método correto
                scraper = WebScraper()
                html_content = scraper.download_page(url, on_progress=on_status_change)

                if html_content:
                    self.db.update_html_repositorio(res_id, html_content)
                    self._update_step("Sucesso: HTML do repositório atualizado.", on_status_change)
                else:
                    self._update_step("Falha: Não foi possível obter o HTML do repositório.", on_status_change)

                if callback_refresh:
                    callback_refresh()

            except Exception as e:
                self.db.log_event(f"Erro no Scrap do Repositório: {str(e)}")
                self._update_step(f"Erro: {str(e)}", on_status_change)

        threading.Thread(target=task, daemon=True).start()

    def extract_from_search_engine(self, res_id, on_status_change, callback_refresh):
        """
        Acionada pelo menu de contexto. Extrai dados institucionais 
        diretamente do HTML da BDTD salvo na Guia 4.
        """
        def task():
            try:
                html = self.db.get_html_buscador(res_id)
                url = self.db.get_link_by_id(res_id) 

                if not html:
                    self._update_step("Erro: Faça o Scrap do Buscador primeiro.", on_status_change)
                    return

                self._update_step("BDTD: Analisando metadados institucional...", on_status_change)
                
                # A factory selecionará o BDTDParser (VuFind)
                parser = self.factory.get_parser(url, html)
                data = parser.extract_pure_soup(html, url)
                
                # Atualiza Sigla, Univ, Programa e Link PDF no banco
                self.db.update_parser_data(res_id, data)
                
                self._update_step(f"Sucesso: {data.get('sigla')} identificado.", on_status_change)
                if callback_refresh: callback_refresh()

            except Exception as e:
                self.db.log_event(f"Erro no parser do buscador: {str(e)}")
                self._update_step(f"Falha: {str(e)}", on_status_change)

        threading.Thread(target=task, daemon=True).start()

    def open_html_buscador_in_browser(self, res_id):
        """Recupera o HTML da Guia 4 do banco e abre no navegador padrão."""
        html = self.db.get_html_buscador(res_id)
        if html:
            self._open_temp_html(html, f"buscador_{res_id}")

    def open_html_repositorio_in_browser(self, res_id):
        """Recupera o HTML da Guia 5 do banco e abre no navegador padrão."""
        html = self.db.get_html_repositorio(res_id)
        if html:
            self._open_temp_html(html, f"repositorio_{res_id}")

    def _open_temp_html(self, content, prefix):
        """Cria um arquivo temporário e o abre no navegador."""
        try:
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', prefix=prefix, encoding='utf-8') as f:
                f.write(content)
                temp_path = f.name
            webbrowser.open(f"file://{os.path.abspath(temp_path)}")
        except Exception as e:
            print(f"Erro ao abrir HTML no navegador: {e}")

    def get_unique_domains(self):
        """Retorna domínios únicos em ORDEM ALFABÉTICA."""
        try:
            links = self.db.get_all_repository_links()
            domains = set()
            for link in links:
                if link and link != "-":
                    domain = urlparse(link).netloc
                    if domain: domains.add(domain)
            return sorted(list(domains)) # ORDEM ALFABÉTICA
        except Exception as e:
            self.db.log_event(f"Erro ao obter domínios: {e}")
            return []

    def open_html_in_browser(self, res_id, source="buscador"):
        """
        Unifica a abertura de HTML do banco no navegador padrão (Chrome/Edge/etc).
        Recupera o conteúdo da Guia 4 ou 5 e utiliza arquivo temporário seguro.
        """
        try:
            html = self.db.get_html_buscador(res_id) if source == "buscador" else self.db.get_html_repositorio(res_id)
            
            if not html:
                self.db.log_event(f"Aviso: Conteúdo de {source} não disponível no banco para ID {res_id}.")
                return False

            # Usa o método interno de criação de arquivo temporário
            self._open_temp_html(html, f"{source}_{res_id}")
            self.db.log_event(f"Conteúdo de {source} aberto no navegador.")
            return True
        except Exception as e:
            self.db.log_event(f"Falha na visualização externa: {str(e)}")
            return False
