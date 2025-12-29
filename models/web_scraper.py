import requests
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class WebScraper:
    @staticmethod
    def fetch_html(url):
        # Garante esquema da URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text

    @staticmethod
    def detect_pagination(html_content, base_url):
        """
        Analisa o HTML para encontrar a paginação, o número máximo de páginas
        e gera a lista de URLs subsequentes.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Procura pela estrutura indicada pelo usuário: <ul class="pagination">
        pagination_ul = soup.find('ul', class_='pagination')
        
        if not pagination_ul:
            return []

        # Encontra todos os links dentro da paginação
        links = pagination_ul.find_all('a', href=True)
        
        max_page = 1
        template_href = None
        
        # Regex para encontrar o parâmetro "page=X"
        page_pattern = re.compile(r'[?&]page=(\d+)')

        for link in links:
            href = link['href']
            match = page_pattern.search(href)
            
            if match:
                page_num = int(match.group(1))
                if page_num > max_page:
                    max_page = page_num
                    # Guarda este href como modelo (template)
                    template_href = href

        if max_page <= 1 or not template_href:
            return []

        # Gera as URLs para as páginas seguintes (de 2 até max_page)
        urls_to_scrape = []
        for i in range(2, max_page + 1):
            # Substitui o page=X original pelo novo número
            new_href = page_pattern.sub(f'page={i}', template_href)
            # Corrige se o regex substituiu o caractere de início (? ou &) incorretamente
            if 'page=' not in new_href: 
                # Fallback simples caso regex falhe na substituição exata
                pass 
            else:
                # Resolve URL relativa para absoluta usando a URL original do registro
                full_url = urljoin(base_url, new_href)
                urls_to_scrape.append((i, full_url))
                
        return urls_to_scrape