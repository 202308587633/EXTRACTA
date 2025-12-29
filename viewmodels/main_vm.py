import threading
from urllib.parse import urlparse
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
                self._update_step("Validando URL informada...", on_status_change)
                if not url.strip():
                    raise ValueError("A URL não pode estar vazia.")

                full_url = url if url.startswith(('http://', 'https://')) else 'https://' + url
                
                self._update_step(f"Analisando domínio de: {full_url}...", on_status_change)
                parsed = urlparse(full_url)
                engine = parsed.netloc if parsed.netloc else "website"
                ano = datetime.now().year

                self._update_step(f"Conectando a {engine}... (Aguardando resposta)", on_status_change)
                html = WebScraper.fetch_html(full_url)
                
                tamanho_kb = len(html) / 1024
                self._update_step(f"Download concluído ({tamanho_kb:.2f} KB). Salvando...", on_status_change)
                
                self.db.insert_scrape(
                    engine=engine,
                    termo=full_url,
                    ano=str(ano),
                    pagina=1,
                    html_source=html
                )
                
                self._update_step(f"Processo finalizado! Salvo em '{engine}'.", on_status_change)
            
            except Exception as e:
                erro_msg = str(e)
                self.db.log_event(f"ERRO: {erro_msg}")
                on_error(erro_msg)

        threading.Thread(target=task, daemon=True).start()

    def delete_record(self, rowid, termo, callback_refresh):
        """Remove o registro e atualiza a UI."""
        try:
            self.db.delete_scrape(rowid)
            self.db.log_event(f"Registro excluído: {termo}")
            if callback_refresh:
                callback_refresh()
        except Exception as e:
            self.db.log_event(f"Erro ao excluir: {str(e)}")

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