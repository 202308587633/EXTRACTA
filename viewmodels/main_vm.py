import threading
from models.db_handler import DatabaseHandler
from models.web_scraper import WebScraper

class MainViewModel:
    def __init__(self):
        self.db = DatabaseHandler()

    def perform_scrape(self, url, on_success, on_error):
        """
        Executa o scrap em uma thread separada para não travar a UI.
        Recebe callbacks (funções) para atualizar a UI ao terminar.
        """
        def task():
            try:
                if not url.strip():
                    raise ValueError("A URL não pode estar vazia.")

                # 1. Scrap
                html = WebScraper.fetch_html(url)
                
                # 2. Salvar no Banco
                self.db.insert_scrape(url, html)
                
                # 3. Notificar sucesso
                on_success(f"Sucesso! {len(html)} caracteres salvos.")
            
            except Exception as e:
                on_error(str(e))

        # Inicia a thread
        threading.Thread(target=task, daemon=True).start()