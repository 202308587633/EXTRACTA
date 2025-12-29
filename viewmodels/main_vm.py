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

    def _update_step(self, message, callback):
        self.db.log_event(message)
        if callback:
            callback(message)

    def perform_scrape(self, url, on_status_change, on_error):
        def task():
            try:
                self._update_step("Validando URL...", on_status_change)
                if not url.strip():
                    raise ValueError("A URL não pode estar vazia.")

                full_url = url if url.startswith(('http://', 'https://')) else 'https://' + url
                
                parsed = urlparse(full_url)
                engine = parsed.netloc if parsed.netloc else "website"
                ano = datetime.now().year

                self._update_step(f"Baixando conteúdo de {engine}...", on_status_change)
                html = WebScraper.fetch_html(full_url)
                
                self._update_step("Gravando HTML e link_busca no banco...", on_status_change)
                
                # O parâmetro full_url é passado para o campo link_busca
                self.db.insert_scrape(
                    engine=engine,
                    termo=full_url,
                    ano=str(ano),
                    pagina=1,
                    html_source=html,
                    link_busca=full_url
                )
                
                self._update_step(f"Processo finalizado com sucesso!", on_status_change)
            
            except Exception as e:
                erro_msg = str(e)
                self.db.log_event(f"ERRO: {erro_msg}")
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
        """
        Lógica para encontrar paginação e raspar páginas seguintes.
        """
        def task():
            try:
                # 1. Recuperar o registro original
                record = self.db.get_scrape_full_details(rowid)
                if not record:
                    return
                
                engine, termo_original, ano, pagina_inicial, html_source = record
                
                self._update_step("Analisando HTML para encontrar paginação...", on_status_change)

                # 2. Encontrar o total de páginas no HTML usando Regex
                matches = re.findall(r'page=(\d+)', html_source)
                if not matches:
                    self._update_step("Nenhuma paginação detectada no HTML.", on_status_change)
                    return

                max_page = max(map(int, matches))

                if max_page <= 1:
                    self._update_step("Apenas uma página detectada.", on_status_change)
                    return

                self._update_step(f"Paginação detectada! Total: {max_page} páginas.", on_status_change)

                # 3. Loop de captura
                parsed_url = urlparse(termo_original)
                query_params = parse_qs(parsed_url.query)

                for p in range(2, max_page + 1):
                    self._update_step(f"Capturando página {p} de {max_page}...", on_status_change)
                    
                    query_params['page'] = [str(p)]
                    new_query = urlencode(query_params, doseq=True)
                    new_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, 
                                          parsed_url.params, new_query, parsed_url.fragment))

                    time.sleep(1) # Pausa ética
                    
                    new_html = WebScraper.fetch_html(new_url)
                    self.db.insert_scrape(engine, termo_original, ano, p, new_html, new_url)

                self._update_step(f"Ciclo finalizado. {max_page} páginas processadas.", on_status_change)
                if callback_refresh:
                    callback_refresh()

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
        def task():
            try:
                self._update_step("Analisando HTML da página...", on_status_change)
                record = self.db.get_scrape_full_details(rowid)
                if not record: return
                
                html_content = record[4]
                soup = BeautifulSoup(html_content, 'html.parser')
                results = soup.select('.result.card-results')

                extracted_to_db = []
                for res in results:
                    # 1. Título e Link do Buscador (dentro da tag h2 > a)
                    title_tag = res.select_one('h2 a.title')
                    titulo = title_tag.get_text(strip=True) if title_tag else "-"
                    link_buscador = title_tag['href'] if title_tag else "-"
                    if link_buscador.startswith('/'):
                        link_buscador = "https://bdtd.ibict.br" + link_buscador

                    # 2. Autor (link que contém /Author/ no href)
                    author_tag = res.select_one('a[href*="/Author/"]')
                    autor = author_tag.get_text(strip=True) if author_tag else "-"

                    # 3. Link do Repositório (expressão "Acessar documento")
                    repo_tag = res.find('a', string=lambda s: s and "Acessar documento" in s)
                    link_repositorio = repo_tag['href'] if repo_tag else "-"

                    extracted_to_db.append((titulo, autor, link_buscador, link_repositorio, rowid))

                if extracted_to_db:
                    self.db.insert_extracted_data(extracted_to_db)
                    self._update_step(f"Extraídos {len(extracted_to_db)} itens com sucesso.", on_status_change)
                
                if callback_refresh: callback_refresh()

            except Exception as e:
                self.db.log_event(f"Erro na extração: {str(e)}")
                if on_error: on_error(str(e))

        threading.Thread(target=task, daemon=True).start()

    def get_research_results(self):
        return self.db.fetch_extracted_data()

    def scrape_buscador_link(self, pesquisa_id, url, on_status_change, callback_display):
        """Realiza o scrap do link interno do buscador e salva no BD."""
        def task():
            try:
                self._update_step(f"Acessando link do buscador: {url[:50]}...", on_status_change)
                
                # Usa o WebScraper já implementado para baixar o HTML
                html = WebScraper.fetch_html(url)
                
                # Salva no banco de dados
                self.db.update_html_buscador(pesquisa_id, html)
                
                self._update_step("HTML do buscador salvo com sucesso!", on_status_change)
                
                if callback_display:
                    callback_display(html)
            except Exception as e:
                self.db.log_event(f"Erro no scrap do buscador: {str(e)}")
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
        """Faz o scrap do link final (repositório) de forma assíncrona."""
        def task():
            try:
                if not url or url == "-":
                    self._update_step("Erro: Link do repositório inválido.", on_status_change)
                    return

                self._update_step(f"Acessando Repositório: {url[:50]}...", on_status_change)
                
                # Reutiliza o WebScraper para baixar o HTML do repositório
                html = WebScraper.fetch_html(url)
                
                self.db.update_html_repositorio(pesquisa_id, html)
                self._update_step("HTML do repositório salvo com sucesso!", on_status_change)
                
                if callback_display:
                    callback_display(html)
            except Exception as e:
                self.db.log_event(f"Erro no scrap do repositório: {str(e)}")
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
        """Extrai sigla e nome da universidade do HTML do buscador já salvo."""
        def task():
            try:
                html = self.db.get_html_buscador(res_id)
                if not html:
                    self._update_step("Erro: HTML do buscador não encontrado. Faça o scrap primeiro.", on_status_change)
                    return

                self._update_step("Analisando metadados da universidade...", on_status_change)
                soup = BeautifulSoup(html, 'html.parser')
                
                # 1. Extração da Sigla (Baseado no ID oculto comum no VuFind)
                # Exemplo: <input type="hidden" value="USP_..." class="hiddenId">
                sigla = "-"
                id_input = soup.select_one('input.hiddenId')
                if id_input and id_input.get('value'):
                    val = id_input.get('value')
                    if '_' in val:
                        sigla = val.split('_')[0]

                # 2. Extração do Nome da Universidade
                # Geralmente encontra-se em tabelas de metadados ou breadcrumbs
                nome = "-"
                # Tenta encontrar em linhas de tabela que mencionam Instituição ou universidade
                for tr in soup.find_all('tr'):
                    header = tr.find('th')
                    if header and any(x in header.get_text().lower() for x in ["instituição", "universidade"]):
                        data = tr.find('td')
                        if data:
                            nome = data.get_text(strip=True)
                            break
                
                # Se não achou na tabela, tenta meta tags (comum no BDTD/VuFind)
                if nome == "-":
                    meta_univ = soup.find('meta', {'name': 'citation_publisher'})
                    if meta_univ:
                        nome = meta_univ.get('content', strip=True)

                self.db.update_univ_data(res_id, sigla, nome)
                self._update_step(f"Dados da universidade ({sigla}) obtidos!", on_status_change)
                
                if callback_refresh:
                    callback_refresh()

            except Exception as e:
                self.db.log_event(f"Erro ao extrair universidade: {str(e)}")
                self._update_step(f"Erro: {str(e)}", on_status_change)

        threading.Thread(target=task, daemon=True).start()
        
