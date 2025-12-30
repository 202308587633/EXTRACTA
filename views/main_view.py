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
        Orquestra a interface com abas e uma barra de status global no rodapé.
        """
        # 1. Painel de Abas (Tabview)
        # pady inferior reduzido para 0 para colar na barra de status
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.tab_home = self.tabview.add("Scraper")
        self.tab_data = self.tabview.add("Histórico")
        self.tab_res = self.tabview.add("Pesquisas")
        self.tab_urls = self.tabview.add("Raízes de URLs")
        self.tab_html_busc = self.tabview.add("Conteúdo Buscador")
        self.tab_html_repo = self.tabview.add("Conteúdo Repositório")

        # 2. Inicialização das Abas (Instanciação das Classes Modulares)
        
        # Guia 4: URLs (Raízes)
        self.url_roots_view = UrlRootsTab(self.tab_urls, self.vm)
        self.url_roots_view.pack(fill="both", expand=True)

        # Guia 3: Pesquisas (Passa callback para atualizar URLs)
        self.research_view = ResearchTab(
            self.tab_res, 
            self.vm, 
            self.update_status_ui, 
            self.url_roots_view.update_url_roots_list
        )
        self.research_view.pack(fill="both", expand=True)

        # Guia 2: Histórico (Passa callback para carregar pesquisas)
        self.history_view = HistoryTab(
            self.tab_data, 
            self.vm, 
            self.update_status_ui, 
            self.research_view.load_research_data
        )
        self.history_view.pack(fill="both", expand=True)

        # Guia 1: Home/Scraper (Passa callbacks de status e erro)
        self.home_view = HomeTab(
            self.tab_home, 
            self.vm, 
            self.update_status_ui, 
            self.on_error
        )
        self.home_view.pack(fill="both", expand=True)

        # Configuração das abas de texto (Guias 5 e 6)
        self._setup_html_viewers()

        # 3. BARRA DE STATUS GLOBAL (Rodapé)
        self.status_frame = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color="#2b2b2b")
        self.status_frame.pack(fill="x", side="bottom")

        # Rótulo de status alinhado à esquerda
        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="Pronto para iniciar.", 
            font=("Roboto", 11),
            text_color="silver"
        )
        self.status_label.pack(side="left", padx=15, pady=2)

    def _setup_html_viewers(self):
        """Campos de texto para visualização de código fonte."""
        self.txt_html_busc = ctk.CTkTextbox(self.tab_html_busc, wrap="none", font=("Consolas", 12))
        self.txt_html_busc.pack(fill="both", expand=True, padx=10, pady=10)

        self.txt_html_repo = ctk.CTkTextbox(self.tab_html_repo, wrap="none", font=("Consolas", 12))
        self.txt_html_repo.pack(fill="both", expand=True, padx=10, pady=10)

    def update_status_ui(self, message):
        """Atualiza a barra de status global e gerencia o estado dos botões."""
        # Garante execução na thread da UI
        self.after(0, lambda: self._safe_status_update(message))

    def _safe_status_update(self, message):
        """Lógica interna de atualização segura."""
        if not self.winfo_exists(): return
        
        self.status_label.configure(text=message, text_color="white")
        
        # Verifica palavras-chave de conclusão para reabilitar botões
        msg_lower = message.lower()
        keywords = ["finalizado", "finalizada", "concluída", "sucesso", "erro", "expandidas"]
        
        if any(kw in msg_lower for kw in keywords):
            self._reall_buttons()

    def _reall_buttons(self):
        """Reabilita botões em todas as abas."""
        if hasattr(self, 'home_view'):
            self.home_view.btn_scrape.configure(state="normal")
        
        if hasattr(self, 'history_view'):
            self.history_view.btn_extract_all.configure(state="normal", text="📥 Extrair Tudo para Pesquisas")
            self.history_view.btn_paginate_all.configure(state="normal", text="🔍 Buscar Todas Páginas (Lote)")
            self.history_view.load_history_list()
        
        # Retorna a cor do status para o padrão após concluir
        self.status_label.configure(text_color="silver")

    def on_error(self, error_msg):
        """Exibe erros em destaque na barra global."""
        self.update_status_ui(f"Erro: {error_msg}")
        self.status_label.configure(text_color="#ff5555") # Vermelho claro
        self._reall_buttons()

    def display_buscador_html(self, html):
        self.txt_html_busc.configure(state="normal")
        self.txt_html_busc.delete("0.0", "end")
        self.txt_html_busc.insert("0.0", html)
        self.tabview.set("Conteúdo Buscador")

    def display_repositorio_html(self, html):
        self.txt_html_repo.configure(state="normal")
        self.txt_html_repo.delete("0.0", "end")
        self.txt_html_repo.insert("0.0", html)
        self.tabview.set("Conteúdo Repositório")