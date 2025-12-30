import tkinter as tk
import customtkinter as ctk

class HistoryTab(ctk.CTkFrame):
    def __init__(self, master, vm, update_status_callback, load_research_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.vm = vm
        self.update_status_ui = update_status_callback
        self.load_research_data = load_research_callback
        
        self.history_buttons = []
        
        self.selected_row_id = None
        self.selected_row_termo = None
        self.selected_row_page = None
        
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface da aba Histórico com lista e botões de ação."""
        self.history_container = ctk.CTkFrame(self)
        self.history_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Painel Esquerdo: Lista de Capturas
        self.list_frame = ctk.CTkScrollableFrame(self.history_container, width=220, label_text="Capturas")
        self.list_frame.pack(side="left", fill="y", padx=(0, 5))
        
        # Painel Direito: Conteúdo e Ações
        self.content_frame = ctk.CTkFrame(self.history_container)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # Frame para botões de ação superiores
        self.action_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=5, pady=5)

        self.btn_refresh = ctk.CTkButton(self.action_frame, text="🔄 Atualizar Lista", command=self.load_history_list, height=28)
        self.btn_refresh.pack(side="left", fill="x", expand=True, padx=2)

        self.btn_extract_all = ctk.CTkButton(
            self.action_frame, 
            text="📥 Extrair Tudo para Pesquisas", 
            fg_color="#1f6aa5", 
            command=self.trigger_batch_extraction,
            height=28
        )
        self.btn_extract_all.pack(side="left", fill="x", expand=True, padx=2)

        self.btn_paginate_all = ctk.CTkButton(
            self.action_frame, 
            text="🔍 Buscar Todas Páginas (Lote)", 
            fg_color="#8B0000",
            command=self.trigger_batch_pagination,
            height=28
        )
        self.btn_paginate_all.pack(side="left", fill="x", expand=True, padx=2)

        # Visualização de Conteúdo
        self.txt_content = ctk.CTkTextbox(self.content_frame, wrap="word", font=("Consolas", 12))
        self.txt_content.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Menu de Contexto (TKinter nativo para CTK)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.load_history_list()

    def load_history_list(self):
        if not self.list_frame.winfo_exists():
            return

        for btn in self.history_buttons:
            if btn.winfo_exists():
                btn.destroy()
        self.history_buttons.clear()

        data = self.vm.get_history()
        if not data:
            return

        for row in data:
            display_text = f"Pág {row[4]}: {row[1][:20]}..."
            
            btn = ctk.CTkButton(
                self.list_frame, 
                text=display_text, 
                fg_color="transparent", 
                border_width=1,
                command=lambda r=row: self.display_content(r)
            )
            btn.pack(fill="x", pady=2)
            
            btn.bind("<Button-3>", lambda e, rid=row[0], rt=row[1], rp=row[4]: 
                     self.show_context_menu(e, rid, rt, rp))
            
            self.history_buttons.append(btn)

    def display_content(self, row_data):
        """Exibe o HTML convertido em texto na área de visualização."""
        self.txt_content.configure(state="normal")
        self.txt_content.delete("0.0", "end")
        self.txt_content.insert("0.0", self.vm.render_html_to_text(row_data[3]))
        self.txt_content.configure(state="disabled")

    def show_context_menu(self, event, row_id, termo, page):
        """Gera o menu de contexto para itens individuais."""
        self.selected_row_id, self.selected_row_termo, self.selected_row_page = row_id, termo, page
        self.context_menu.delete(0, "end")
        self.context_menu.add_command(label="Abrir no Navegador", command=self.open_current_in_browser)
        self.context_menu.add_command(label="📊 Extrair Dados", command=self.trigger_extraction)
        
        if page == 1: 
            self.context_menu.add_command(label="🔍 Buscar Todas Páginas", command=self.trigger_pagination_scrape)
            
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Excluir", command=self.delete_current_selection)
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def open_current_in_browser(self):
        if self.selected_row_id: self.vm.open_in_browser(self.selected_row_id)

    def trigger_extraction(self):
        if self.selected_row_id:
            self.vm.extract_research_data(self.selected_row_id, self.update_status_ui, None, self.load_research_data)

    def trigger_pagination_scrape(self):
        if self.selected_row_id: 
            self.vm.process_pagination(self.selected_row_id, self.update_status_ui, self.load_history_list)

    def trigger_batch_extraction(self):
        data = self.vm.get_history()
        if data:
            self.btn_extract_all.configure(state="disabled", text="Processando...")
            row_ids = [row[0] for row in data]
            self.vm.batch_extract_research_data(row_ids, self.update_status_ui, None, self.load_research_data)

    def trigger_batch_pagination(self):
        data = self.vm.get_history()
        if data:
            target_ids = [row[0] for row in data if row[4] == 1]
            if target_ids:
                self.btn_paginate_all.configure(state="disabled", text="Paginando...")
                self.vm.batch_process_pagination(target_ids, self.update_status_ui, self.load_history_list)

    def delete_current_selection(self):
        if self.selected_row_id: 
            self.vm.delete_record(self.selected_row_id, self.selected_row_termo, self.load_history_list)
