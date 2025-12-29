import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UDFParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UDF", universidade="Centro Universitário do Distrito Federal")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {'sigla': self.sigla, 'universidade': self.universidade, 'programa': '-', 'link_pdf': '-'}

        # Extração do Programa via Breadcrumb (Penúltimo item)
        breads = soup.select('li.breadcrumb-item')
        if len(breads) >= 2:
            data['programa'] = breads[-2].get_text(strip=True)

        # Extração do PDF via Meta Tag
        pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if pdf_meta:
            data['link_pdf'] = urljoin(url, pdf_meta.get('content'))

        return data