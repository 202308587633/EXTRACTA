import tkinter as tk
import customtkinter as ctk
from viewmodels.main_vm import MainViewModel
from tkinter import ttk 

class MainView(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Modern Scraper & Logger")
        self.geometry("900x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.vm = MainViewModel()
        self.setup_ui()

    def setup_ui(self):
        """Inicializa a interface com as cinco guias."""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_home = self.tabview.add("Scraper")
        self.tab_data = self.tabview.add("Histórico")
        self.tab_res = self.tabview.add("Pesquisas")
        self.tab_html_busc = self.tabview.add("Conteúdo Buscador")
        self.tab_html_repo = self.tabview.add("Conteúdo Repositório")

        self._setup_history_tab()
        self._setup_research_tab()
        self._setup_html_buscador_tab()
        self._setup_html_repositorio_tab()
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
        self.status_label = ctk.CTkLabel(self.status_frame, text="Aguardando...", text_color="gray")
        self.status_label.pack(side="left")
        self.btn_logs = ctk.CTkButton(self.status_frame, text="[Ver Logs]", width=60, fg_color="transparent", 
                                      command=self.open_log_viewer, cursor="hand2")
        self.btn_logs.pack(side="left", padx=(5, 0))

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
        self.context_menu = tk.Menu(self, tearoff=0)
        self.load_history_list()

    def _setup_research_tab(self):
        self.res_container = ctk.CTkFrame(self.tab_res)
        self.res_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Colunas atualizadas para incluir Sigla e Universidade
        cols = ("titulo", "autor", "link_busc", "link_repo", "sigla", "univ")
        self.tree = ttk.Treeview(self.res_container, columns=cols, show="headings")
        
        headers = {
            "titulo": "Pesquisa", 
            "autor": "Autor", 
            "link_busc": "Link Buscador", 
            "link_repo": "Link Repositório",
            "sigla": "Sigla IES", 
            "univ": "Universidade"
        }
        
        # Configuração de cabeçalhos com comando de ordenação por clique
        for col, text in headers.items():
            self.tree.heading(
                col, 
                text=text, 
                command=lambda c=col: self.sort_treeview(c, False)
            )
            self.tree.column(col, width=120)
            
        scrollbar = ttk.Scrollbar(self.res_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Menu de Contexto Aprimorado
        self.research_menu = tk.Menu(self, tearoff=0)
        self.research_menu.add_command(label="📥 Scrap Link Buscador", command=self.trigger_buscador_scrap)
        self.research_menu.add_command(label="🎓 Obter Dados da Universidade", command=self.trigger_extract_univ) # Nova Opção
        self.research_menu.add_command(label="🚀 Scrap Link Repositório", command=self.trigger_repositorio_scrap)
        self.research_menu.add_separator()
        self.research_menu.add_command(label="📄 Ver HTML Buscador (Guia 4)", command=self.view_saved_buscador_html)
        self.research_menu.add_command(label="📄 Ver HTML Repositório (Guia 5)", command=self.view_saved_repositorio_html)
        self.research_menu.add_separator()
        self.research_menu.add_command(label="🌐 Abrir HTML Buscador no Navegador", command=lambda: self.open_html_preview("buscador"))
        self.research_menu.add_command(label="🌐 Abrir HTML Repositório no Navegador", command=lambda: self.open_html_preview("repositorio"))
        
        self.tree.bind("<Button-3>", self.show_research_context_menu)
        self.load_research_data()

    def _setup_html_buscador_tab(self):
        self.txt_html_busc = ctk.CTkTextbox(self.tab_html_busc, wrap="none", font=("Consolas", 12))
        self.txt_html_busc.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_html_repositorio_tab(self):
        self.txt_html_repo = ctk.CTkTextbox(self.tab_html_repo, wrap="none", font=("Consolas", 12))
        self.txt_html_repo.pack(fill="both", expand=True, padx=10, pady=10)

    # --- Lógica de Interface ---
    def on_scrape_click(self):
        url = self.url_entry.get()
        self.btn_scrape.configure(state="disabled")
        self.vm.perform_scrape(url, self.update_status_ui, self.on_error)

    def update_status_ui(self, message):
        self.status_label.configure(text=message)
        if "finalizado" in message.lower() or "processadas" in message.lower():
            self.btn_scrape.configure(state="normal")
            self.load_history_list()

    def on_error(self, error_msg):
        self.btn_scrape.configure(state="normal")
        self.status_label.configure(text=f"Erro: {error_msg}", text_color="red")

    def open_log_viewer(self):
        log_window = ctk.CTkToplevel(self)
        log_window.title("Logs")
        log_window.geometry("500x400")
        log_window.attributes("-topmost", True)
        txt_logs = ctk.CTkTextbox(log_window, wrap="word")
        txt_logs.pack(fill="both", expand=True, padx=10, pady=10)
        logs = self.vm.get_system_logs()
        for created_at, message in logs:
            txt_logs.insert("end", f"[{created_at}] {message}\n")
        txt_logs.configure(state="disabled")

    def load_history_list(self):
        for widget in self.list_frame.winfo_children(): widget.destroy()
        data = self.vm.get_history()
        for row in data:
            display_text = f"Pág {row[4]}: {row[1][:20]}..."
            btn = ctk.CTkButton(self.list_frame, text=display_text, fg_color="transparent", border_width=1,
                                command=lambda r=row: self.display_content(r))
            btn.pack(fill="x", pady=2)
            btn.bind("<Button-3>", lambda e, rid=row[0], rt=row[1], rp=row[4]: self.show_context_menu(e, rid, rt, rp))

    def load_research_data(self):
        """Carrega os resultados incluindo as colunas de universidade (Sigla e Nome)."""
        for item in self.tree.get_children(): 
            self.tree.delete(item)
        
        data = self.vm.get_research_results()
        for row in data:
            # Garante que campos vazios ou None apareçam como "-" para não quebrar a tabela
            processed_row = [str(val) if val and str(val).strip() != "" else "-" for val in row]
            self.tree.insert("", "end", values=processed_row)

    # --- Menus de Contexto e Ações ---
    def show_context_menu(self, event, row_id, termo, page):
        self.selected_row_id, self.selected_row_termo, self.selected_row_page = row_id, termo, page
        self.context_menu.delete(0, "end")
        self.context_menu.add_command(label="Abrir no Navegador", command=self.open_current_in_browser)
        self.context_menu.add_command(label="📊 Extrair Dados", command=self.trigger_extraction)
        if page == 1: self.context_menu.add_command(label="🔍 Buscar Todas Páginas", command=self.trigger_pagination_scrape)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Excluir", command=self.delete_current_selection)
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def show_research_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            res_id = self._get_id_from_selected()
            
            # Verifica se o buscador já possui HTML salvo
            html_busc = self.vm.fetch_saved_html_buscador(res_id)
            state_dependent = "normal" if html_busc else "disabled"
            
            # Aplica o estado aos menus que dependem do HTML do buscador
            self.research_menu.entryconfig("🎓 Obter Dados da Universidade", state=state_dependent)
            self.research_menu.entryconfig("🚀 Scrap Link Repositório", state=state_dependent)
            
            # Validação Navegador
            html_repo = self.vm.db.get_html_repositorio(res_id)
            self.research_menu.entryconfig("🌐 Abrir HTML Buscador no Navegador", state="normal" if html_busc else "disabled")
            self.research_menu.entryconfig("🌐 Abrir HTML Repositório no Navegador", state="normal" if html_repo else "disabled")
            
            self.research_menu.tk_popup(event.x_root, event.y_root)
            
    def _get_id_from_selected(self):
        selected = self.tree.selection()
        if not selected: return None
        titulo = self.tree.item(selected[0])['values'][0]
        res = self.vm.db.conn.execute("SELECT id FROM pesquisas_extraidas WHERE titulo=?", (titulo,)).fetchone()
        return res[0] if res else None

    # --- Gatilhos de Scrap e Exibição ---
    def trigger_extraction(self):
        if self.selected_row_id:
            self.vm.extract_research_data(self.selected_row_id, self.update_status_ui, self.on_error, self.load_research_data)

    def trigger_buscador_scrap(self):
        selected = self.tree.selection()
        if selected:
            url, res_id = self.tree.item(selected[0])['values'][2], self._get_id_from_selected()
            self.vm.scrape_buscador_link(res_id, url, self.update_status_ui, self.display_buscador_html)

    def trigger_repositorio_scrap(self):
        selected = self.tree.selection()
        if selected:
            url, res_id = self.tree.item(selected[0])['values'][3], self._get_id_from_selected()
            if url != "-": self.vm.scrape_repositorio_link(res_id, url, self.update_status_ui, self.display_repositorio_html)

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

    def view_saved_buscador_html(self):
        res_id = self._get_id_from_selected()
        if res_id: 
            html = self.vm.fetch_saved_html_buscador(res_id)
            self.display_buscador_html(html if html else "Nenhum conteúdo salvo.")

    def view_saved_repositorio_html(self):
        res_id = self._get_id_from_selected()
        if res_id: 
            html = self.vm.db.get_html_repositorio(res_id)
            self.display_repositorio_html(html if html else "Nenhum conteúdo salvo.")

    def open_html_preview(self, tipo):
        """Abre o conteúdo solicitado no navegador."""
        res_id = self._get_id_from_selected()
        if not res_id: 
            return

        # Busca o conteúdo correto baseado no tipo solicitado no menu
        if tipo == "buscador":
            html_content = self.vm.fetch_saved_html_buscador(res_id)
        else:
            # Acessa diretamente via banco se não houver método na VM
            html_content = self.vm.db.get_html_repositorio(res_id)

        if html_content:
            # Chama o novo método genérico criado na ViewModel
            success, msg = self.vm.preview_html_content_in_browser(html_content)
            if not success: 
                self.on_error(msg)
        else:
            self.on_error(f"Nenhum conteúdo de {tipo} encontrado para esta pesquisa.")

    # --- Outros auxiliares ---
    def open_current_in_browser(self):
        if self.selected_row_id: self.vm.open_in_browser(self.selected_row_id)

    def trigger_pagination_scrape(self):
        if self.selected_row_id: self.vm.process_pagination(self.selected_row_id, self.update_status_ui, self.load_history_list)

    def delete_current_selection(self):
        if self.selected_row_id: self.vm.delete_record(self.selected_row_id, self.selected_row_termo, self.load_history_list)

    def display_content(self, row_data):
        self.txt_content.configure(state="normal")
        self.txt_content.delete("0.0", "end")
        self.txt_content.insert("0.0", self.vm.render_html_to_text(row_data[3]))
        self.txt_content.configure(state="disabled")

    def sort_treeview(self, col, reverse):
        """Ordena o conteúdo da Treeview ao clicar no título da coluna."""
        # Obtém todos os dados da coluna selecionada
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        # Realiza a ordenação (alfabética)
        l.sort(reverse=reverse)

        # Move os itens para a nova ordem visual
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Inverte o comportamento para o próximo clique (Alternar entre A-Z e Z-A)
        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))
        
    def trigger_extract_univ(self):
        """Inicia a extração de sigla e nome da universidade através da ViewModel."""
        res_id = self._get_id_from_selected()
        if res_id:
            # Certifique-se de que extract_university_info existe na sua MainViewModel
            self.vm.extract_university_info(res_id, self.update_status_ui, self.load_research_data)
  
