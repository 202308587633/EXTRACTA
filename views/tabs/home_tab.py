import customtkinter as ctk
import urllib.parse

class HomeTab(ctk.CTkFrame):
    def __init__(self, master, vm, update_status_callback, on_error_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.vm = vm
        self.update_status_ui = update_status_callback
        self.on_error = on_error_callback
        
        self.setup_ui()

    def setup_ui(self):
        """Configura a aba Scraper com Comboboxes e campo de URL dinâmico."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True)

        self.label = ctk.CTkLabel(
            container, 
            text="Parâmetros de Pesquisa BDTD", 
            font=("Roboto", 18)
        )
        self.label.pack(pady=(0, 20))

        # Frame para as seleções (Termos e Anos)
        combos_frame = ctk.CTkFrame(container, fg_color="transparent")
        combos_frame.pack(fill="x", pady=10)

        # 1. Combobox para Termos de Pesquisa solicitados
        self.combo_termos = ctk.CTkComboBox(
            combos_frame, 
            width=220, 
            values=[
                "jurimetria", "inteligência artificial", "análise de discurso", 
                "algoritmo", "direito digital", "tecnologia da informação"
            ],
            command=self._update_url_from_selection
        )
        self.combo_termos.set("jurimetria")
        self.combo_termos.pack(side="left", padx=5)

        # 2. Combobox para Anos (2020 a 2025)
        self.combo_anos = ctk.CTkComboBox(
            combos_frame, 
            width=100,
            values=[str(ano) for ano in range(2020, 2026)],
            command=self._update_url_from_selection
        )
        self.combo_anos.set("2020")
        self.combo_anos.pack(side="left", padx=5)

        # Campo de entrada que exibe a URL final montada
        self.url_entry = ctk.CTkEntry(container, placeholder_text="URL gerada...", width=600)
        self.url_entry.pack(pady=10)
        
        # Inicializa a URL com os valores padrão
        self._update_url_from_selection()

        # Botão de ação principal
        self.btn_scrape = ctk.CTkButton(
            container, 
            text="Iniciar Extração", 
            command=self.on_scrape_click
        )
        self.btn_scrape.pack(pady=20)

        # Rótulo de status (atualizado via callback da thread principal)
        self.status_label = ctk.CTkLabel(container, text="Pronto para iniciar.", text_color="gray")
        self.status_label.pack(pady=5)

    def _update_url_from_selection(self, _=None):
        """Monta a URL da BDTD dinamicamente conforme os parâmetros selecionados."""
        termo = self.combo_termos.get()
        ano = self.combo_anos.get()
        
        base_url = "https://bdtd.ibict.br/vufind/Search/Results"
        params = [
            ('join', 'AND'),
            ('bool0[]', 'AND'),
            ('lookfor0[]', f'"{termo}"'), # Termo entre aspas
            ('type0[]', 'AllFields'),
            ('lookfor0[]', 'direito'),    # Filtro fixo de assunto
            ('type0[]', 'Subject'),
            ('illustration', '-1'),
            ('daterange[]', 'publishDate'),
            ('publishDatefrom', ano),
            ('publishDateto', ano)
        ]
        
        # Constrói a query string mantendo os colchetes dos parâmetros
        full_url = f"{base_url}?{urllib.parse.urlencode(params, safe='[]')}"
        
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, full_url)

    def on_scrape_click(self):
        """Inicia o processo de captura via ViewModel."""
        url = self.url_entry.get()
        termo_amigavel = self.combo_termos.get()
        ano_selecionado = self.combo_anos.get()

        if not url:
            self.on_error("A URL não foi gerada corretamente.")
            return

        self.btn_scrape.configure(state="disabled")
        # Dispara a tarefa na ViewModel garantindo a persistência do termo e ano
        self.vm.perform_scrape(
            url, 
            termo_amigavel, 
            ano_selecionado, 
            self.update_status_ui, 
            self.on_error
        )