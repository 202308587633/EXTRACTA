import customtkinter as ctk
from viewmodels.main_vm import MainViewModel

class MainView(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.title("Modern Scraper")
        self.geometry("600x400")
        ctk.set_appearance_mode("System")  # Dark/Light mode automático
        ctk.set_default_color_theme("blue")

        # Inicializa ViewModel
        self.vm = MainViewModel()

        # Layout
        self.setup_ui()

    def setup_ui(self):
        # Criação das Abas
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        self.tab_home = self.tabview.add("Scraper")
        self.tab_data = self.tabview.add("Histórico") # Aba extra solicitada

        # --- Conteúdo da Aba 1 (Home) ---
        self.label = ctk.CTkLabel(self.tab_home, text="Insira a URL para extração", font=("Roboto", 16))
        self.label.pack(pady=(40, 10))

        self.url_entry = ctk.CTkEntry(self.tab_home, placeholder_text="ex: google.com", width=400)
        self.url_entry.pack(pady=10)

        self.btn_scrape = ctk.CTkButton(self.tab_home, text="Iniciar Extração", command=self.on_scrape_click)
        self.btn_scrape.pack(pady=20)

        self.status_label = ctk.CTkLabel(self.tab_home, text="", text_color="gray")
        self.status_label.pack(pady=10)

        # --- Conteúdo da Aba 2 (Histórico - Placeholder) ---
        lbl_info = ctk.CTkLabel(self.tab_data, text="Visualização de dados futuros aqui.")
        lbl_info.pack(pady=50)

    def on_scrape_click(self):
        url = self.url_entry.get()
        
        # UI Feedback imediato
        self.btn_scrape.configure(state="disabled", text="Processando...")
        self.status_label.configure(text="Conectando...", text_color="yellow")

        # Chama a ViewModel
        self.vm.perform_scrape(url, self.on_success, self.on_error)

    def on_success(self, message):
        # Atualiza UI (precisa ser thread-safe, mas CTK lida bem com isso no geral)
        self.btn_scrape.configure(state="normal", text="Iniciar Extração")
        self.status_label.configure(text=message, text_color="green")
        self.url_entry.delete(0, 'end')

    def on_error(self, error_msg):
        self.btn_scrape.configure(state="normal", text="Iniciar Extração")
        self.status_label.configure(text=f"Erro: {error_msg}", text_color="red")