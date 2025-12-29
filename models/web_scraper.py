import requests

class WebScraper:
    @staticmethod
    def fetch_html(url):
        # Adiciona http se o usuário esquecer
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Levanta erro se a página não carregar
        return response.text