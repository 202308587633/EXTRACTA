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
        """
        Inicializa a interface garantindo que a aba de URLs e seus componentes 
        existam antes de qualquer carregamento de dados.
        """
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_home = self.tabview.add("Scraper")
        self.tab_data = self.tabview.add("Histórico")
        self.tab_res = self.tabview.add("Pesquisas")
        self.tab_urls = self.tabview.add("Raízes de URLs") # Nova Guia
        self.tab_html_busc = self.tabview.add("Conteúdo Buscador")
        self.tab_html_repo = self.tabview.add("Conteúdo Repositório")

        # ORDEM DE INICIALIZAÇÃO CORRIGIDA: URL Roots antes de Pesquisas
        self._setup_history_tab()
        self._setup_url_roots_tab()    # Inicializa scroll_urls primeiro
        self._setup_research_tab()     # load_research_data agora pode rodar com segurança
        self._setup_html_buscador_tab()
        self._setup_html_repositorio_tab()
        self._setup_home_tab()

    def _setup_home_tab(self):
        """Configura a aba Scraper com Comboboxes para montagem dinâmica da URL BDTD."""
        container = ctk.CTkFrame(self.tab_home, fg_color="transparent")
        container.pack(expand=True)

        self.label = ctk.CTkLabel(container, text="Parâmetros de Pesquisa BDTD", font=("Roboto", 18))
        self.label.pack(pady=(0, 20))

        # --- SEÇÃO DE COMBOBOXES SOLICITADAS ---
        combos_frame = ctk.CTkFrame(container, fg_color="transparent")
        combos_frame.pack(fill="x", pady=10)

        # 1. Combobox para Termos
        termos_opcoes = ["jurimetria", "inteligência artificial", "análise de discurso", 
                         "algoritmo", "direito digital", "tecnologia da informação"]
        self.combo_termos = ctk.CTkComboBox(
            combos_frame, 
            values=termos_opcoes,
            command=self._update_url_from_selection,
            width=200
        )
        self.combo_termos.set("jurimetria")
        self.combo_termos.pack(side="left", padx=5)

        # 2. Combobox para Anos (2020 a 2025)
        anos_opcoes = [str(ano) for ano in range(2020, 2026)]
        self.combo_anos = ctk.CTkComboBox(
            combos_frame, 
            values=anos_opcoes,
            command=self._update_url_from_selection,
            width=100
        )
        self.combo_anos.set("2020")
        self.combo_anos.pack(side="left", padx=5)

        # Campo de entrada que exibirá a URL montada
        self.url_entry = ctk.CTkEntry(container, placeholder_text="URL gerada aparecerá aqui", width=600)
        self.url_entry.pack(pady=10)

        self._update_url_from_selection() # Gera URL inicial baseada nos defaults

        self.btn_scrape = ctk.CTkButton(container, text="Iniciar Extração", command=self.on_scrape_click)
        self.btn_scrape.pack(pady=20)

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
        """Configura a aba de pesquisas e o menu de contexto."""
        self.res_container = ctk.CTkFrame(self.tab_res)
        self.res_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Definição das 8 colunas
        cols = ("titulo", "autor", "link_busc", "link_repo", "sigla", "univ", "programa", "pdf")
        self.tree = ttk.Treeview(self.res_container, columns=cols, show="headings")
        
        headers = {
            "titulo": "Pesquisa", "autor": "Autor", "link_busc": "Link Buscador", 
            "link_repo": "Link Repositório", "sigla": "Sigla", 
            "univ": "Universidade", "programa": "Programa", "pdf": "Link PDF"
        }
        
        for col, text in headers.items():
            self.tree.heading(col, text=text, command=lambda c=col: self.sort_treeview(c, False))
            self.tree.column(col, width=100)
            
        scrollbar = ttk.Scrollbar(self.res_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- CRIAÇÃO DO MENU DE CONTEXTO ---
        # Definimos os labels como variáveis para evitar erros de digitação entre as funções
        self.LABEL_EXTRACT = "🎓 Extrair Sigla/Univ/Programa/PDF"
        self.LABEL_PDF = "🌐 Abrir Link PDF no Navegador"

        self.research_menu = tk.Menu(self, tearoff=0)
        self.research_menu.add_command(label="📥 Scrap Link Buscador", command=self.trigger_buscador_scrap)
        self.research_menu.add_command(label="🚀 Scrap Link Repositório", command=self.trigger_repositorio_scrap)
        self.research_menu.add_separator()
        self.research_menu.add_command(label=self.LABEL_EXTRACT, command=self.trigger_extract_univ)
        self.research_menu.add_separator()
        self.research_menu.add_command(label="📄 Ver HTML Buscador (Guia 4)", command=self.view_saved_buscador_html)
        self.research_menu.add_command(label="📄 Ver HTML Repositório (Guia 5)", command=self.view_saved_repositorio_html)
        self.research_menu.add_separator()
        self.research_menu.add_command(label=self.LABEL_PDF, command=self.open_pdf_link)
        
        self.tree.bind("<Button-3>", self.show_research_context_menu)
        self.load_research_data()

    def _setup_html_buscador_tab(self):
        self.txt_html_busc = ctk.CTkTextbox(self.tab_html_busc, wrap="none", font=("Consolas", 12))
        self.txt_html_busc.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_html_repositorio_tab(self):
        self.txt_html_repo = ctk.CTkTextbox(self.tab_html_repo, wrap="none", font=("Consolas", 12))
        self.txt_html_repo.pack(fill="both", expand=True, padx=10, pady=10)

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
        """Mapeia as 8 colunas e atualiza a lista de URLs simultaneamente."""
        for item in self.tree.get_children(): 
            self.tree.delete(item)
        
        data = self.vm.get_research_results()
        for row in data:
            processed_row = [str(val) if val and str(val).strip() != "" else "-" for val in row]
            self.tree.insert("", "end", values=processed_row)
            
        # Atualização simultânea solicitada
        self.update_url_roots_list()

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
        """Menu de contexto com extração de buscador e visualização no navegador."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            res_id = self._get_id_from_selected()
            html_busc = self.vm.fetch_saved_html_buscador(res_id)
            html_repo = self.vm.db.get_html_repositorio(res_id)
            
            self.research_menu.delete(0, "end")
            
            if html_busc:
                self.research_menu.add_command(
                    label="✨ Extrair dados do buscador (Sigla/Univ)", 
                    command=lambda: self.vm.extract_from_search_engine(res_id, self.update_status_ui, self.load_research_data)
                )
                self.research_menu.add_command(
                    label="🌐 Abrir HTML Buscador no Navegador", 
                    command=lambda: self.vm.open_in_browser(res_id) # Reuso do método da VM
                )
                self.research_menu.add_separator()

            self.research_menu.add_command(label=self.LABEL_EXTRACT, command=self.trigger_extract_univ)
            
            if html_repo:
                self.research_menu.add_command(
                    label="🌐 Abrir HTML Repositório no Navegador", 
                    command=lambda: self.vm.preview_html_content_in_browser(html_repo)
                )
            
            self.research_menu.add_separator()
            self.research_menu.add_command(label="📄 Ver HTML Buscador (Guia 4)", command=self.view_saved_buscador_html)
            self.research_menu.add_command(label="📄 Ver HTML Repositório (Guia 5)", command=self.view_saved_repositorio_html)
            self.research_menu.add_command(label=self.LABEL_PDF, command=self.open_pdf_link)
            self.research_menu.tk_popup(event.x_root, event.y_root)
                        
    def _get_id_from_selected(self):
        selected = self.tree.selection()
        if not selected: return None
        titulo = self.tree.item(selected[0])['values'][0]
        res = self.vm.db.conn.execute("SELECT id FROM pesquisas_extraidas WHERE titulo=?", (titulo,)).fetchone()
        return res[0] if res else None

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
        """Inicia a extração refinada (Sigla, Univ, Programa, PDF) usando Parsers."""
        res_id = self._get_id_from_selected()
        if res_id:
            # Chama a ViewModel para processar os dados institucionais e o link do PDF
            self.vm.extract_university_info(res_id, self.update_status_ui, self.load_research_data)

    def open_pdf_link(self):
        selected = self.tree.selection()
        if selected:
            pdf_url = self.tree.item(selected[0], "values")[7] # 8ª coluna
            if pdf_url and pdf_url != "-":
                import webbrowser
                webbrowser.open(pdf_url)

    def _setup_url_roots_tab(self):
        """Configura a guia com botão superior e persistência de domínios."""
        self.frame_url_actions = ctk.CTkFrame(self.tab_urls, fg_color="transparent")
        self.frame_url_actions.pack(fill="x", padx=10, pady=5)

        # Botão solicitado acima do grupo
        self.btn_sync_domains = ctk.CTkButton(
            self.frame_url_actions, 
            text="🔄 Sincronizar e Persistir Domínios (A-Z)", 
            command=self.update_url_roots_list,
            width=300
        )
        self.btn_sync_domains.pack(pady=10)

        self.scroll_urls = ctk.CTkScrollableFrame(
            self.tab_urls, 
            label_text="Filtros de Domínio (Persistidos no Banco)"
        )
        self.scroll_urls.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.domain_vars = {}

    def update_url_roots_list(self):
        """
        Preenche a guia de URLs em ordem alfabética e recupera estados do banco.
        Garante persistência ao marcar/desmarcar.
        """
        if not hasattr(self, 'scroll_urls'): return

        # Busca domínios únicos via VM e estados salvos via DB
        domains = self.vm.get_unique_domains()
        saved_states = self.vm.db.get_domain_states()
        
        for widget in self.scroll_urls.winfo_children(): widget.destroy()
            
        self.domain_vars = {}
        
        for dom in domains:
            # Recupera estado salvo ou define como marcado (True) por padrão
            state = saved_states.get(dom, True)
            var = tk.BooleanVar(value=state)
            
            cb = ctk.CTkCheckBox(
                self.scroll_urls, 
                text=dom, 
                variable=var,
                command=lambda d=dom, v=var: self.vm.db.save_domain_state(d, v.get())
            )
            cb.pack(anchor="w", padx=20, pady=5)
            self.domain_vars[dom] = var
            
            # Se é um domínio novo, persiste no banco imediatamente
            if dom not in saved_states:
                self.vm.db.save_domain_state(dom, True)

    def _update_url_entry(self, _=None):
        """Atualiza a url_entry com base na seleção das Comboboxes."""
        termo = self.combo_termos.get()
        ano = self.combo_anos.get()
        
        if termo == "Selecione o Termo": termo = ""
        if ano == "Selecione o Ano": ano = ""
        
        resultado = f"{termo} {ano}".strip()
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, resultado)

    def _update_url_from_selection(self, _=None):
        """Monta a URL da BDTD dinamicamente conforme o exemplo solicitado."""
        import urllib.parse
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
        
        query_string = urllib.parse.urlencode(params, safe='[]')
        full_url = f"{base_url}?{query_string}"
        
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, full_url)
