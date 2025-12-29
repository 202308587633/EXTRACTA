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

    # (Outros métodos como delete_record, get_history e render_html_to_text permanecem iguais)
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
            
            
