import tkinter as tk
import customtkinter as ctk
from viewmodels.main_vm import MainViewModel

# Importação das abas modularizadas
from views.tabs.home_tab import HomeTab
from views.tabs.history_tab import HistoryTab
from views.tabs.research_tab import ResearchTab
from views.tabs.url_roots_tab import UrlRootsTab

class MainView(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern Scraper & Logger")
        self.geometry("900x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Inicializa a ViewModel única para todas as abas
        self.vm = MainViewModel()
        
        self.setup_ui()

    def setup_ui(self):
        """
        Orquestra a criação das abas, garantindo que as dependências 
        entre componentes sejam respeitadas.
        """
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. Criação dos contentores de abas no Tabview
        self.tab_home = self.tabview.add("Scraper")
        self.tab_data = self.tabview.add("Histórico")
        self.tab_res = self.tabview.add("Pesquisas")
        self.tab_urls = self.tabview.add("Raízes de URLs")
        self.tab_html_busc = self.tabview.add("Conteúdo Buscador")
        self.tab_html_repo = self.tabview.add("Conteúdo Repositório")

        # 2. Inicialização dos componentes (Abas) como frames independentes
        # Nota: A ordem respeita a necessidade de callbacks entre abas
        
        # Aba de URLs (Raízes) - Necessária para ser atualizada pela ResearchTab
        self.url_roots_view = UrlRootsTab(self.tab_urls, self.vm)
        self.url_roots_view.pack(fill="both", expand=True)

        # Aba de Pesquisas - Passa o callback para atualizar a aba de URLs
        self.research_view = ResearchTab(
            self.tab_res, 
            self.vm, 
            self.update_status_ui, 
            self.url_roots_view.update_url_roots_list
        )
        self.research_view.pack(fill="both", expand=True)

        # Aba de Histórico - Passa o callback para carregar dados de pesquisa
        self.history_view = HistoryTab(
            self.tab_data, 
            self.vm, 
            self.update_status_ui, 
            self.research_view.load_research_data
        )
        self.history_view.pack(fill="both", expand=True)

        # Aba Home (Scraper)
        self.home_view = HomeTab(
            self.tab_home, 
            self.vm, 
            self.update_status_ui, 
            self.on_error
        )
        self.home_view.pack(fill="both", expand=True)

        # 3. Configuração das abas de visualização de HTML
        self._setup_html_viewers()

    def _setup_html_viewers(self):
        """Configura os campos de texto para visualização de código fonte."""
        self.txt_html_busc = ctk.CTkTextbox(self.tab_html_busc, wrap="none", font=("Consolas", 12))
        self.txt_html_busc.pack(fill="both", expand=True, padx=10, pady=10)

        self.txt_html_repo = ctk.CTkTextbox(self.tab_html_repo, wrap="none", font=("Consolas", 12))
        self.txt_html_repo.pack(fill="both", expand=True, padx=10, pady=10)

    def update_status_ui(self, message):
        """Encaminha atualizações de status para a HomeTab de forma segura."""
        if hasattr(self, 'home_view'):
            # Usa after(0) para garantir execução na thread da UI
            self.after(0, lambda: self.home_view.status_label.configure(text=message))
            
            # Reabilita botões se a mensagem indicar conclusão
            msg_lower = message.lower()
            if any(kw in msg_lower for kw in ["finalizado", "finalizada", "concluída", "sucesso", "erro"]):
                self.after(0, self._reall_buttons)

    def _reall_buttons(self):
        """Garante a reabilitação dos botões em todos os componentes."""
        self.home_view.btn_scrape.configure(state="normal")
        self.history_view.btn_extract_all.configure(state="normal", text="📥 Extrair Tudo para Pesquisas")
        self.history_view.btn_paginate_all.configure(state="normal", text="🔍 Buscar Todas Páginas (Lote)")
        self.history_view.load_history_list()

    def on_error(self, error_msg):
        """Trata exibição de erros na interface."""
        self.update_status_ui(f"Erro: {error_msg}")
        self.home_view.status_label.configure(text_color="red")
        self._reall_buttons()

    def display_buscador_html(self, html):
        """Exibe o HTML na aba correspondente."""
        self.txt_html_busc.configure(state="normal")
        self.txt_html_busc.delete("0.0", "end")
        self.txt_html_busc.insert("0.0", html)
        self.tabview.set("Conteúdo Buscador")

    def display_repositorio_html(self, html):
        """Exibe o HTML na aba correspondente."""
        self.txt_html_repo.configure(state="normal")
        self.txt_html_repo.delete("0.0", "end")
        self.txt_html_repo.insert("0.0", html)
        self.tabview.set("Conteúdo Repositório")