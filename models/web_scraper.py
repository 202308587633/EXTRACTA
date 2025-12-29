import os
import time
import requests
import urllib3
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

# Desativar avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WebScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # Assume que o driver está na raiz do projeto
        self.driver_path = os.path.join(os.getcwd(), "msedgedriver.exe")

    def download_page(self, url, on_progress=None):
        """Tenta requests; se houver bloqueio de bot (Anubis/reCAPTCHA), usa Selenium."""
        try:
            if on_progress: on_progress(f"Conectando: {url[:40]}...")
            response = requests.get(url, headers=self.headers, verify=False, timeout=15)
            
            html_content = response.text.lower()
            # Detecta bloqueios que retornam 200 OK mas não mostram conteúdo
            is_blocked = (
                response.status_code in [403, 401] or 
                "recaptcha" in html_content or 
                "not a bot" in html_content or 
                "anubis" in html_content or
                "verificando sua sessão" in html_content
            )

            if is_blocked:
                if on_progress: on_progress("Desafio de bot/bloqueio detectado. Iniciando navegador...")
                return self._download_with_selenium(url, on_progress)
            
            response.raise_for_status()
            return response.text
        except Exception:
            if on_progress: on_progress("Falha no acesso direto. Tentando via navegador...")
            return self._download_with_selenium(url, on_progress)
                
    def _download_with_selenium(self, url, on_progress=None):
        """Abre o navegador Edge para contornar proteções antirrobô."""
        if not os.path.exists(self.driver_path):
            if on_progress: on_progress("Erro: msedgedriver.exe não encontrado na raiz.")
            return None

        edge_options = Options()
        edge_options.add_argument("--headless")  # Executa sem abrir janela visual
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument(f"user-agent={self.headers['User-Agent']}")

        service = Service(self.driver_path)
        driver = None
        try:
            driver = webdriver.Edge(service=service, options=edge_options)
            driver.get(url)
            
            # Aguarda o carregamento do conteúdo dinâmico (DSpace 7/9)
            time.sleep(6) 
            
            html = driver.page_source
            if on_progress: on_progress("Conteúdo capturado com sucesso via Selenium.")
            return html
        except Exception as e:
            if on_progress: on_progress(f"Falha no Selenium: {str(e)[:30]}")
            return None
        finally:
            if driver:
                driver.quit()
    