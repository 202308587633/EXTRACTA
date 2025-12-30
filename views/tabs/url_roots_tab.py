import tkinter as tk
import customtkinter as ctk

class UrlRootsTab(ctk.CTkFrame):
    def __init__(self, master, vm, **kwargs):
        super().__init__(master, **kwargs)
        self.vm = vm
        
        # Dicionário para rastrear as variáveis dos checkboxes em memória
        self.domain_vars = {}
        
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface da guia com botão de sincronização e lista de filtros."""
        self.frame_url_actions = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_url_actions.pack(fill="x", padx=10, pady=5)

        # Botão centralizado para sincronizar os domínios encontrados nas pesquisas
        self.btn_sync_domains = ctk.CTkButton(
            self.frame_url_actions, 
            text="🔄 Sincronizar e Persistir Domínios (A-Z)", 
            command=self.update_url_roots_list,
            width=300
        )
        self.btn_sync_domains.pack(pady=10)

        # Área rolável para exibir os domínios únicos
        self.scroll_urls = ctk.CTkScrollableFrame(
            self, 
            label_text="Filtros de Domínio (Persistidos no Banco)"
        )
        self.scroll_urls.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def update_url_roots_list(self):
        """
        Sincroniza os domínios em ordem alfabética e recupera os estados salvos no banco.
        Garante a persistência imediata ao marcar ou desmarcar.
        """
        if not self.scroll_urls.winfo_exists():
            return

        # Busca domínios únicos via VM e estados salvos via DB
        domains = self.vm.get_unique_domains()
        saved_states = self.vm.db.get_domain_states()
        
        # Limpa a lista atual antes de reconstruir
        for widget in self.scroll_urls.winfo_children():
            widget.destroy()
            
        self.domain_vars = {}
        
        for dom in domains:
            # Recupera estado salvo (True por padrão se for um novo domínio)
            state = saved_states.get(dom, True)
            var = tk.BooleanVar(value=state)
            
            # Cria o checkbox vinculado à função de salvamento do banco
            cb = ctk.CTkCheckBox(
                self.scroll_urls, 
                text=dom, 
                variable=var,
                command=lambda d=dom, v=var: self.vm.db.save_domain_state(d, v.get())
            )
            cb.pack(anchor="w", padx=20, pady=5)
            self.domain_vars[dom] = var
            
            # Se for um domínio novo, persiste o estado padrão imediatamente
            if dom not in saved_states:
                self.vm.db.save_domain_state(dom, True)