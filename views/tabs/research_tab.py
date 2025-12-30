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
        """Configura a aba de pesquisas com a Treeview de 10 colunas."""
        self.res_container = ctk.CTkFrame(self)
        self.res_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Definição das 10 colunas solicitadas
        cols = ("titulo", "autor", "link_busc", "link_repo", "sigla", "univ", "prog", "pdf", "termo", "ano")
        self.tree = ttk.Treeview(self.res_container, columns=cols, show="headings")
        
        headers = {
            "titulo": "Pesquisa", "autor": "Autor", "link_busc": "Buscador", 
            "link_repo": "Repos.", "sigla": "Sigla", "univ": "Univ", 
            "prog": "Programa", "pdf": "PDF", "termo": "Termo Busca", "ano": "Ano Filtro"
        }
        
        for col, text in headers.items():
            self.tree.heading(col, text=text, command=lambda c=col: self.sort_treeview(c, False))
            # Colunas de termo e ano ligeiramente mais estreitas
            self.tree.column(col, width=90 if col in ["termo", "ano"] else 110)
        
        scrollbar = ttk.Scrollbar(self.res_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Menu de Contexto
        self.research_menu = tk.Menu(self, tearoff=0)
        self.tree.bind("<Button-3>", self.show_research_context_menu)
        
        self.load_research_data()

    def load_research_data(self):
        """Carrega os resultados da ViewModel e atualiza a interface."""
        for item in self.tree.get_children(): 
            self.tree.delete(item)
        
        data = self.vm.get_research_results()
        for row in data:
            # Processa as 10 colunas garantindo '-' em campos vazios
            processed_row = [str(val) if val and str(val).strip() != "" else "-" for val in row]
            self.tree.insert("", "end", values=processed_row)
            
        # Sincroniza a lista de URLs (Raízes) sempre que os dados mudam
        self.update_url_roots_list()

    def sort_treeview(self, col, reverse):
        """Ordena o conteúdo da Treeview ao clicar no título da coluna."""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    def show_research_context_menu(self, event):
        """Menu de contexto com visualização no navegador e extração refinada."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            res_id = self._get_id_from_selected()
            
            # Verifica conteúdos guardados para habilitar opções de visualização
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
                    command=lambda: self.vm.open_html_in_browser(res_id, "buscador")
                )
                self.research_menu.add_separator()

            self.research_menu.add_command(label=self.LABEL_EXTRACT, command=self.trigger_extract_univ)
            
            if html_repo:
                self.research_menu.add_command(
                    label="🌐 Abrir HTML Repositório no Navegador", 
                    command=lambda: self.vm.open_html_in_browser(res_id, "repositorio")
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
        """Dispara o Parser para extrair Sigla, Universidade, Programa e PDF."""
        res_id = self._get_id_from_selected()
        if res_id:
            self.vm.extract_university_info(res_id, self.update_status_ui, self.load_research_data)

    def open_pdf_link(self):
        """Abre o link do PDF no navegador padrão."""
        selected = self.tree.selection()
        if selected:
            pdf_url = self.tree.item(selected[0], "values")[7] # 8ª coluna (índice 7)
            if pdf_url and pdf_url != "-":
                import webbrowser
                webbrowser.open(pdf_url)