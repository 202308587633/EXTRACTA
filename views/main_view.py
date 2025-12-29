import tkinter as tk
import customtkinter as ctk
from viewmodels.main_vm import MainViewModel

class MainView(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern Scraper & Logger")
        self.geometry("800x600")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.vm = MainViewModel()
        self.setup_ui()

    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_home = self.tabview.add("Scraper")
        self.tab_data = self.tabview.add("Histórico")

        self._setup_history_tab()
        self._setup_home_tab()

    def _setup_home_tab(self):
        container = ctk.CTkFrame(self.tab_home, fg_color="transparent")
        container.pack(expand=True)

        self.label = ctk.CTkLabel(container, text="Insira a URL para extração", font=("Roboto", 18))
        self.label.pack(pady=(0, 10))

        self.url_entry = ctk.CTkEntry(container, placeholder_text="ex: python.org", width=400)
        self.url_entry.pack(pady=10)

        self.btn_scrape = ctk.CTkButton(container, text="Iniciar Extração", command=self.on_scrape_click)
        self.btn_scrape.pack(pady=20)

        self.status_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.status_frame.pack(pady=10)

        self.status_label = ctk.CTkLabel(self.status_frame, text="Carregando...", text_color="gray")
        self.status_label.pack(side="left")

        self.btn_logs = ctk.CTkButton(
            self.status_frame, 
            text="[Ver Logs]", 
            width=60,
            fg_color="transparent", 
            text_color=("#3B8ED0", "#1F6AA5"),
            hover_color=("gray90", "gray20"),
            font=("Roboto", 12, "underline"),
            cursor="hand2",
            command=self.open_log_viewer
        )
        self.btn_logs.pack(side="left", padx=(5, 0))

        last_msg = self.vm.get_initial_status()
        self.update_status_ui(last_msg)

    def _setup_history_tab(self):
        self.history_container = ctk.CTkFrame(self.tab_data)
        self.history_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.list_frame = ctk.CTkScrollableFrame(self.history_container, width=220, label_text="Capturas")
        self.list_frame.pack(side="left", fill="y", padx=(0, 5))

        self.content_frame = ctk.CTkFrame(self.history_container)
        self.content_frame.pack(side="right", fill="both", expand=True)

        self.btn_refresh = ctk.CTkButton(self.content_frame, text="Atualizar Lista", command=self.load_history_list, height=25)
        self.btn_refresh.pack(fill="x", padx=5, pady=5)

        self.txt_content = ctk.CTkTextbox(self.content_frame, wrap="word", font=("Consolas", 12))
        self.txt_content.pack(fill="both", expand=True, padx=5, pady=5)
        
        # O Menu é criado dinamicamente no momento do clique agora
        self.context_menu = tk.Menu(self, tearoff=0)
        
        # Variáveis de estado para seleção
        self.selected_row_id = None 
        self.selected_row_termo = None
        self.selected_row_page = 1

        self.load_history_list()

    def on_scrape_click(self):
        url = self.url_entry.get()
        self.btn_scrape.configure(state="disabled")
        self.vm.perform_scrape(url, self.update_status_ui, self.on_error)

    def update_status_ui(self, message):
        self.status_label.configure(text=message, text_color=("gray10", "gray90"))
        # Verifica se finalizou um processo simples ou de paginação
        if "finalizado" in message.lower() or "processadas" in message.lower():
            self.btn_scrape.configure(state="normal", text="Iniciar Extração")
            self.url_entry.delete(0, 'end')
            self.load_history_list()

    def on_error(self, error_msg):
        self.btn_scrape.configure(state="normal", text="Iniciar Extração")
        self.status_label.configure(text=f"Erro: {error_msg}", text_color="red")

    def open_log_viewer(self):
        log_window = ctk.CTkToplevel(self)
        log_window.title("Registros de Sistema (Logs)")
        log_window.geometry("500x400")
        log_window.attributes("-topmost", True)

        ctk.CTkLabel(log_window, text="Histórico Completo de Execução", font=("Roboto", 16, "bold")).pack(pady=10)

        txt_logs = ctk.CTkTextbox(log_window, wrap="word", font=("Consolas", 11))
        txt_logs.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        logs = self.vm.get_system_logs()

        if not logs:
            txt_logs.insert("0.0", "Nenhum registro encontrado.")
        else:
            for created_at, message in logs:
                line = f"[{created_at}] {message}\n"
                txt_logs.insert("end", line)

        txt_logs.configure(state="disabled")

    def load_history_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        # Agora data contém 5 elementos: id, termo, data, html, pagina
        data = self.vm.get_history()

        if not data:
            ctk.CTkLabel(self.list_frame, text="Nenhum registro.").pack(pady=10)
            return

        for row in data:
            # row: 0=id, 1=termo, 2=data, 3=html, 4=pagina
            url_clean = row[1].replace("https://", "").replace("http://", "")[:20]
            pagina = row[4]
            display_text = f"Pág {pagina}: {url_clean}...\n{str(row[2])[:10]}"
            
            btn = ctk.CTkButton(
                self.list_frame, 
                text=display_text, 
                fg_color="transparent", 
                border_width=1,
                anchor="w",
                command=lambda r=row: self.display_content(r)
            )
            btn.pack(fill="x", pady=2)
            
            # Passamos row[4] (pagina) para o manipulador do clique direito
            btn.bind("<Button-3>", lambda event, rid=row[0], rtermo=row[1], rpage=row[4]: self.show_context_menu(event, rid, rtermo, rpage))

    def show_context_menu(self, event, row_id, termo, page):
        """Constrói o menu dinamicamente baseado na página."""
        self.selected_row_id = row_id
        self.selected_row_termo = termo
        self.selected_row_page = page
        
        # Limpa o menu anterior e recria
        self.context_menu.delete(0, "end")
        
        self.context_menu.add_command(label="Abrir no Navegador", command=self.open_current_in_browser)
        
        # LÓGICA SOLICITADA: Só exibe se for página 1
        if self.selected_row_page == 1:
            self.context_menu.add_command(label="🔍 Buscar Todas as Páginas", command=self.trigger_pagination_scrape)
        
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Excluir Registro", command=self.delete_current_selection)
        
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def open_current_in_browser(self):
        if self.selected_row_id:
            self.vm.open_in_browser(self.selected_row_id)

    def trigger_pagination_scrape(self):
        """Inicia a varredura das páginas seguintes."""
        if self.selected_row_id:
            # Passa a função de atualização de UI e de Status
            self.vm.process_pagination(self.selected_row_id, self.update_status_ui, self.load_history_list)

    def delete_current_selection(self):
        if self.selected_row_id:
            self.vm.delete_record(self.selected_row_id, self.selected_row_termo, self.load_history_list)
            self.txt_content.configure(state="normal")
            self.txt_content.delete("0.0", "end")
            self.txt_content.configure(state="disabled")

    def display_content(self, row_data):
        raw_html = row_data[3]
        rendered_text = self.vm.render_html_to_text(raw_html)
        
        self.txt_content.configure(state="normal")
        self.txt_content.delete("0.0", "end")
        
        header = f"URL: {row_data[1]}\nPÁGINA: {row_data[4]}\nDATA: {row_data[2]}\n{'-'*60}\n\n"
        self.txt_content.insert("0.0", header + rendered_text)
        
        self.txt_content.configure(state="disabled")