import tkinter as tk
import customtkinter as ctk
from tkinter import ttk

class ResearchTab(ctk.CTkFrame):
    def __init__(self, master, vm, update_status_callback, update_url_roots_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.vm = vm
        self.update_status_ui = update_status_callback
        self.update_url_roots_list = update_url_roots_callback
        
        # Labels fixos para o menu de contexto
        self.LABEL_EXTRACT = "🎓 Extrair Dados Institucionais"
        self.LABEL_PDF = "📄 Abrir Link do PDF"
        
        self.setup_ui()

    def setup_ui(self):
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_process_all = ctk.CTkButton(
            self.action_frame,
            text="⚙️ Processar Metadados em Lote (Parsers)",
            fg_color="#2b7a78",
            hover_color="#17252a",
            height=30,
            command=self.trigger_batch_parser
        )
        self.btn_process_all.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_refresh = ctk.CTkButton(
            self.action_frame,
            text="🔄 Recarregar Tabela",
            fg_color="#555555",
            height=30,
            width=150,
            command=self.load_research_data
        )
        self.btn_refresh.pack(side="right")

        style = ttk.Style()
        style.theme_use("default")
        
        style.configure("Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            borderwidth=0,
            rowheight=25,
            font=("Roboto", 10))
            
        style.map("Treeview", background=[('selected', '#1f6aa5')])
        
        style.configure("Treeview.Heading",
            background="#1a1a1a",
            foreground="silver",
            relief="flat",
            font=("Roboto", 10, "bold"))
            
        style.map("Treeview.Heading", background=[('active', '#252525')])

        self.res_container = ctk.CTkFrame(self, fg_color="transparent")
        self.res_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        cols = ("titulo", "autor", "link_busc", "link_repo", "sigla", "univ", "prog", "pdf", "termo", "ano")
        self.tree = ttk.Treeview(self.res_container, columns=cols, show="headings")
        
        headers = {
            "titulo": "Pesquisa", "autor": "Autor", "link_busc": "Buscador", 
            "link_repo": "Repos.", "sigla": "Sigla", "univ": "Univ", 
            "prog": "Programa", "pdf": "PDF", "termo": "Termo Busca", "ano": "Ano Filtro"
        }
        
        for col, text in headers.items():
            self.tree.heading(col, text=text, command=lambda c=col: self.sort_treeview(c, False))
            width = 90 if col in ["termo", "ano", "sigla", "pdf"] else 120
            self.tree.column(col, width=width)
        
        vsb = ttk.Scrollbar(self.res_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.res_container, orient="horizontal", command=self.tree.xview)
        
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        self.res_container.grid_rowconfigure(0, weight=1)
        self.res_container.grid_columnconfigure(0, weight=1)
        
        self.research_menu = tk.Menu(self, tearoff=0)
        self.tree.bind("<Button-3>", self.show_research_context_menu)
        
        self.load_research_data()

    def load_research_data(self):
        """Carrega os resultados da ViewModel e atualiza a interface."""
        # Limpa dados antigos
        for item in self.tree.get_children(): 
            self.tree.delete(item)
        
        data = self.vm.get_research_results()
        for row in data:
            # Processa as 10 colunas garantindo '-' em campos vazios
            processed_row = [str(val) if val and str(val).strip() != "" else "-" for val in row]
            self.tree.insert("", "end", values=processed_row)
            
        # Sincroniza a lista de URLs (Raízes) sempre que os dados mudam
        if self.update_url_roots_list:
            self.update_url_roots_list()

    def sort_treeview(self, col, reverse):
        """Ordena o conteúdo da Treeview ao clicar no título da coluna."""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    def show_research_context_menu(self, event):
        """Menu de contexto atualizado com callbacks de atualização pontual."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            res_id = self._get_id_from_selected()
            
            # Recupera dados para validar opções
            html_busc = self.vm.fetch_saved_html_buscador(res_id)
            html_repo = self.vm.db.get_html_repositorio(res_id)
            
            self.research_menu.delete(0, "end")
            
            # 1. Ações de Scrap
            self.research_menu.add_command(
                label="🔍 Fazer Scrap da Página de Busca (Guia 4)", 
                command=self.trigger_buscador_scrap
            )
            self.research_menu.add_command(
                label="🌐 Fazer Scrap do Repositório (Guia 5)", 
                command=self.trigger_repositorio_scrap
            )
            self.research_menu.add_separator()

            # 2. Ações de Extração (COM OTIMIZAÇÃO)
            if html_busc:
                self.research_menu.add_command(
                    label="✨ Extrair dados do buscador (Sigla/Univ)", 
                    command=lambda: self.vm.extract_from_search_engine(
                        res_id, 
                        self.update_status_ui, 
                        # Callback otimizado: passa o item atual (item) e o ID
                        lambda: self.update_single_row(item, res_id)
                    )
                )
            
            self.research_menu.add_command(
                label=self.LABEL_EXTRACT, 
                command=self.trigger_extract_univ
            )
            self.research_menu.add_separator()

            # 3. Visualização e PDF
            if html_busc:
                self.research_menu.add_command(
                    label="🌐 Abrir HTML Buscador (Navegador)", 
                    command=lambda: self.vm.open_html_in_browser(res_id, "buscador")
                )
                self.research_menu.add_command(
                    label="📄 Ver HTML Buscador (Interno)", 
                    command=self.view_saved_buscador_html
                )
                
            if html_repo:
                self.research_menu.add_command(
                    label="🌐 Abrir HTML Repositório (Navegador)", 
                    command=lambda: self.vm.open_html_in_browser(res_id, "repositorio")
                )
                self.research_menu.add_command(
                    label="📄 Ver HTML Repositório (Interno)", 
                    command=self.view_saved_repositorio_html
                )
            
            self.research_menu.add_separator()
            self.research_menu.add_command(label=self.LABEL_PDF, command=self.open_pdf_link)
            
            self.research_menu.tk_popup(event.x_root, event.y_root)

    def _get_id_from_selected(self):
        """Recupera o ID da base de dados através do título selecionado."""
        selected = self.tree.selection()
        if not selected: return None
        titulo = self.tree.item(selected[0])['values'][0]
        res = self.vm.db.conn.execute("SELECT id FROM pesquisas_extraidas WHERE titulo=?", (titulo,)).fetchone()
        return res[0] if res else None

    def trigger_extract_univ(self):
        """Dispara o Parser e atualiza apenas a linha selecionada ao finalizar."""
        selected = self.tree.selection()
        if not selected: return
        
        # Obtém o identificador visual (IID) e o ID do banco
        item_iid = selected[0]
        res_id = self._get_id_from_selected()
        
        if res_id:
            self.vm.extract_university_info(
                res_id, 
                self.update_status_ui, 
                # Callback otimizado: atualiza só esta linha
                lambda: self.update_single_row(item_iid, res_id)
            )

    def open_pdf_link(self):
        """Abre o link do PDF no navegador padrão."""
        selected = self.tree.selection()
        if selected:
            # A 8ª coluna (índice 7) contém o link do PDF
            pdf_url = self.tree.item(selected[0], "values")[7]
            if pdf_url and pdf_url != "-":
                import webbrowser
                webbrowser.open(pdf_url)

    def trigger_buscador_scrap(self):
        """Dispara a captura do HTML da página de detalhes da BDTD."""
        selected = self.tree.selection()
        if selected:
            url = self.tree.item(selected[0])['values'][2] # Coluna Link Buscador
            res_id = self._get_id_from_selected()
            
            # Callback para exibir na aba interna (acessa MainView via parent chain)
            display_callback = self.master.master.master.display_buscador_html if hasattr(self.master.master.master, 'display_buscador_html') else None
            
            self.vm.scrape_buscador_link(res_id, url, self.update_status_ui, display_callback)

    def trigger_repositorio_scrap(self):
        """Dispara a captura do HTML diretamente do repositório da universidade."""
        selected = self.tree.selection()
        if selected:
            url = self.tree.item(selected[0])['values'][3] # Coluna Link Repositório
            res_id = self._get_id_from_selected()
            if url != "-":
                display_callback = self.master.master.master.display_repositorio_html if hasattr(self.master.master.master, 'display_repositorio_html') else None
                
                self.vm.scrape_repositorio_link(res_id, url, self.update_status_ui, display_callback)

    def view_saved_buscador_html(self):
        """Envia o HTML salvo para a aba de visualização no MainView."""
        res_id = self._get_id_from_selected()
        if res_id:
            html = self.vm.fetch_saved_html_buscador(res_id)
            if hasattr(self.master.master.master, 'display_buscador_html'):
                self.master.master.master.display_buscador_html(html if html else "Nenhum conteúdo salvo.")

    def view_saved_repositorio_html(self):
        """Envia o HTML salvo para a aba de visualização no MainView."""
        res_id = self._get_id_from_selected()
        if res_id:
            html = self.vm.db.get_html_repositorio(res_id)
            if hasattr(self.master.master.master, 'display_repositorio_html'):
                self.master.master.master.display_repositorio_html(html if html else "Nenhum conteúdo salvo.")

    def update_single_row(self, item_iid, res_id):
        """Atualiza apenas a linha solicitada na Treeview sem recarregar tudo."""
        # Garante que a atualização da GUI ocorra na thread principal
        self.after(0, lambda: self._safe_single_update(item_iid, res_id))

    def _safe_single_update(self, item_iid, res_id):
        """Lógica interna de atualização da linha."""
        record = self.vm.get_research_row(res_id)
        if record and self.tree.exists(item_iid):
            # Processa valores (None -> "-") mantendo a formatação padrão
            processed_row = [str(val) if val and str(val).strip() != "" else "-" for val in record]
            # Atualiza os valores da linha existente na Treeview
            self.tree.item(item_iid, values=processed_row)
              
    def trigger_batch_extraction(self):
        ids = self.vm.get_filtered_batch_ids()
        
        if not ids:
            self.update_status_ui("Nenhum item encontrado para os domínios marcados na aba 'Raízes de URLs'.")
            return

        self.btn_batch_extract.configure(state="disabled", text=f"Processando {len(ids)} itens...")
        
        def on_finish():
            self.after(0, lambda: self.btn_batch_extract.configure(state="normal", text="🚀 Extrair Dados de Todas as Pesquisas (Lote)"))
            self.after(0, self.load_research_data)

        self.vm.batch_extract_university_info(ids, self.update_status_ui, on_finish)

    def trigger_batch_parser(self):
        self.btn_process_all.configure(state="disabled", text="Processando...")
        
        self.vm.batch_extract_university_info(
            on_status_change=self.update_status_ui,
            callback_refresh=self.on_batch_finish
        )

    def on_batch_finish(self):
        self.load_research_data()
        self.after(0, lambda: self.btn_process_all.configure(state="normal", text="⚙️ Processar Metadados em Lote (Parsers)"))
