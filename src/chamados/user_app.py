from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .config import get_database_path
from .database import Database
from .machine import machine_id, machine_name
from .models import CATEGORIES, PRIORITIES
from .tray import TrayController


class UserApp(tk.Tk):
    def __init__(self, start_minimized: bool = False) -> None:
        super().__init__()
        self.title("Chamados Usuario")
        self.geometry("1140x700")
        self.minsize(980, 620)
        self.start_minimized = start_minimized
        self._is_closing = False

        self.db = Database(get_database_path())
        self.current_machine_id = machine_id()
        self.current_machine_name = machine_name()
        self.tray = TrayController(self, "Chamados Usuario", self._force_close)

        self.requester_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.priority_var = tk.StringVar(value=PRIORITIES[1])
        self.status_var = tk.StringVar(
            value=f"Maquina: {self.current_machine_name} ({self.current_machine_id})"
        )

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close_request)
        self.tray.start()
        self.refresh_tickets()
        self.after(15000, self._auto_refresh)
        if self.start_minimized:
            self.after(400, self._apply_start_mode)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=3)
        root.columnconfigure(1, weight=5)
        root.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(root, text="Novo chamado", padding=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ttk.Label(left, text="Solicitante (opcional)").grid(row=0, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.requester_var).grid(
            row=1, column=0, sticky="ew", pady=(2, 8)
        )

        ttk.Label(left, text="Titulo").grid(row=2, column=0, sticky="w")
        ttk.Entry(left, textvariable=self.title_var).grid(row=3, column=0, sticky="ew", pady=(2, 8))

        selectors = ttk.Frame(left)
        selectors.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        selectors.columnconfigure(0, weight=1)
        selectors.columnconfigure(1, weight=1)

        ttk.Label(selectors, text="Categoria").grid(row=0, column=0, sticky="w")
        ttk.Label(selectors, text="Prioridade").grid(row=0, column=1, sticky="w")
        ttk.Combobox(
            selectors, textvariable=self.category_var, values=CATEGORIES, state="readonly"
        ).grid(row=1, column=0, sticky="ew", padx=(0, 6))
        ttk.Combobox(
            selectors, textvariable=self.priority_var, values=PRIORITIES, state="readonly"
        ).grid(row=1, column=1, sticky="ew")

        ttk.Label(left, text="Descricao").grid(row=5, column=0, sticky="w")
        self.description_text = tk.Text(left, height=11, wrap="word")
        self.description_text.grid(row=6, column=0, sticky="nsew", pady=(2, 10))
        left.rowconfigure(6, weight=1)
        left.columnconfigure(0, weight=1)

        actions = ttk.Frame(left)
        actions.grid(row=7, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        ttk.Button(actions, text="Abrir chamado", command=self.submit_ticket).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ttk.Button(actions, text="Limpar", command=self.clear_form).grid(row=0, column=1, sticky="ew")

        right = ttk.LabelFrame(root, text="Meus chamados (por maquina)", padding=12)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        header = ttk.Frame(right)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Atualizar", command=self.refresh_tickets).grid(row=0, column=1, sticky="e")

        columns = ("protocol", "status", "priority", "title", "updated_at")
        self.tree = ttk.Treeview(right, columns=columns, show="headings", height=12)
        self.tree.heading("protocol", text="Protocolo")
        self.tree.heading("status", text="Status")
        self.tree.heading("priority", text="Prioridade")
        self.tree.heading("title", text="Titulo")
        self.tree.heading("updated_at", text="Atualizado em")

        self.tree.column("protocol", width=130, anchor="w")
        self.tree.column("status", width=145, anchor="center")
        self.tree.column("priority", width=95, anchor="center")
        self.tree.column("title", width=290, anchor="w")
        self.tree.column("updated_at", width=150, anchor="center")
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        scroll = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=1, column=1, sticky="ns")

        self.details = tk.Text(right, height=11, wrap="word", state="disabled")
        self.details.grid(row=2, column=0, sticky="nsew", pady=(10, 0))

    def clear_form(self) -> None:
        self.title_var.set("")
        self.description_text.delete("1.0", tk.END)
        self.category_var.set(CATEGORIES[0])
        self.priority_var.set(PRIORITIES[1])

    def submit_ticket(self) -> None:
        title = self.title_var.get().strip()
        desc = self.description_text.get("1.0", tk.END).strip()
        requester = self.requester_var.get().strip()
        category = self.category_var.get().strip()
        priority = self.priority_var.get().strip()

        if not title:
            messagebox.showwarning("Validacao", "Informe um titulo para o chamado.")
            return
        if len(desc) < 10:
            messagebox.showwarning("Validacao", "A descricao deve ter pelo menos 10 caracteres.")
            return

        try:
            protocol = self.db.create_ticket(
                requester_name=requester,
                machine_name=self.current_machine_name,
                machine_id=self.current_machine_id,
                title=title,
                description=desc,
                category=category,
                priority=priority,
            )
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao abrir chamado.\n{exc}")
            return

        self.clear_form()
        self.refresh_tickets()
        messagebox.showinfo("Sucesso", f"Chamado aberto com protocolo {protocol}.")

    def refresh_tickets(self) -> None:
        try:
            rows = self.db.list_tickets_by_machine(self.current_machine_id)
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao carregar chamados.\n{exc}")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    row["protocol"],
                    row["status"],
                    row["priority"],
                    row["title"],
                    row["updated_at"],
                ),
            )

    def on_tree_select(self, _event: object) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        protocol = self.tree.item(selected[0], "values")[0]
        ticket = self.db.get_ticket(protocol)
        events = self.db.list_events(protocol, limit=8)
        if ticket is None:
            return

        lines = [
            f"Protocolo: {ticket['protocol']}",
            f"Status: {ticket['status']}",
            f"Prioridade: {ticket['priority']}",
            f"Categoria: {ticket['category']}",
            f"Aberto em: {ticket['created_at']}",
            f"Atualizado em: {ticket['updated_at']}",
            f"Encerrado em: {ticket['closed_at'] or '-'}",
            f"Solicitante: {ticket['requester_name'] or '-'}",
            f"Maquina: {ticket['machine_name']} ({ticket['machine_id']})",
            "",
            f"Titulo: {ticket['title']}",
            "",
            "Descricao:",
            ticket["description"],
            "",
            "Ultimos eventos:",
        ]
        for evt in events:
            lines.append(
                f"- {evt['created_at']} | {evt['event_type']} | {evt['event_desc']}"
            )

        self.details.configure(state="normal")
        self.details.delete("1.0", tk.END)
        self.details.insert("1.0", "\n".join(lines))
        self.details.configure(state="disabled")

    def _auto_refresh(self) -> None:
        self.refresh_tickets()
        self.after(15000, self._auto_refresh)

    def _on_close_request(self) -> None:
        if self._is_closing:
            self.destroy()
            return

        if self.tray.available:
            self.tray.hide_window()
            return

        self._force_close()

    def _force_close(self) -> None:
        if self._is_closing:
            return
        self._is_closing = True
        self.tray.stop()
        self.destroy()

    def _apply_start_mode(self) -> None:
        if self.tray.available:
            self.tray.hide_window()
            return
        self.iconify()


def main(start_minimized: bool = False) -> None:
    app = UserApp(start_minimized=start_minimized)
    app.mainloop()


if __name__ == "__main__":
    main()
