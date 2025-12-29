import re
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser

class BDTDParser(BaseParser):
    def __init__(self):
        # Inicializa com valores padrão que serão sobrescritos no extract
        super().__init__(sigla="-", universidade="-")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados diretamente do HTML do buscador BDTD (VuFind).
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {
            'sigla': '-',
            'universidade': '-',
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("BDTD: Analisando metadados do buscador...")

        # 1. Extração da Universidade e Sigla (Tabela principal)
        # O VuFind usa <th> para o rótulo e <td> para o valor
        univ_tag = soup.find('th', string=re.compile(r'Instituição de defesa', re.I))
        if univ_tag:
            td = univ_tag.find_next_sibling('td')
            if td: data['universidade'] = td.get_text(strip=True)
        
        sigla_tag = soup.find('th', string=re.compile(r'Sigla da instituição', re.I))
        if sigla_tag:
            td = sigla_tag.find_next_sibling('td')
            if td: data['sigla'] = td.get_text(strip=True)

        # 2. Extração do Programa (fica em 'Programa de Pós-Graduação' ou 'Departamento')
        prog_tag = soup.find('th', string=re.compile(r'Programa de Pós-Graduação|Departamento', re.I))
        if prog_tag:
            td = prog_tag.find_next_sibling('td')
            if td:
                # Limpa sufixos de sigla no final, ex: "Direito (UDF)" -> "Direito"
                raw_prog = td.get_text(strip=True)
                data['programa'] = re.sub(r'\s*\([A-Z]{2,}\)$', '', raw_prog).strip()

        # 3. Extração do Link do Repositório (coluna Link de acesso)
        # Na BDTD, o link de acesso aponta para a página do repositório final
        link_tag = soup.find('th', string=re.compile(r'Link de acesso', re.I))
        if link_tag:
            a_tag = link_tag.find_next('a', href=True)
            if a_tag:
                data['link_pdf'] = a_tag['href']

        return data