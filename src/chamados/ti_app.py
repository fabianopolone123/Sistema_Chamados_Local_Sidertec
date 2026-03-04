from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .config import get_database_path
from .database import Database
from .machine import machine_name
from .models import OPEN_STATUSES, PRIORITIES, STATUSES


class TIApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Chamados TI")
        self.geometry("1300x760")
        self.minsize(1100, 680)

        self.db = Database(get_database_path())
        self.current_machine_name = machine_name()
        self.selected_protocol: str | None = None

        self.status_filter_var = tk.StringVar(value="TODOS")
        self.priority_filter_var = tk.StringVar(value="TODAS")
        self.search_var = tk.StringVar()
        self.edit_status_var = tk.StringVar(value=STATUSES[0])
        self.assigned_var = tk.StringVar(value=self.current_machine_name)
        self.summary_var = tk.StringVar(value="")

        self._build_ui()
        self.refresh_grid()
        self.after(12000, self._auto_refresh)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=7)
        root.columnconfigure(1, weight=5)
        root.rowconfigure(2, weight=1)

        filters = ttk.LabelFrame(root, text="Filtros", padding=10)
        filters.grid(row=0, column=0, columnspan=2, sticky="ew")
        filters.columnconfigure(6, weight=1)

        ttk.Label(filters, text="Status").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            filters,
            textvariable=self.status_filter_var,
            values=["TODOS", *STATUSES],
            state="readonly",
            width=20,
        ).grid(row=1, column=0, sticky="ew", padx=(0, 6))

        ttk.Label(filters, text="Prioridade").grid(row=0, column=1, sticky="w")
        ttk.Combobox(
            filters,
            textvariable=self.priority_filter_var,
            values=["TODAS", *PRIORITIES],
            state="readonly",
            width=12,
        ).grid(row=1, column=1, sticky="ew", padx=(0, 6))

        ttk.Label(filters, text="Busca (protocolo/titulo/maquina)").grid(row=0, column=2, sticky="w")
        ttk.Entry(filters, textvariable=self.search_var, width=34).grid(
            row=1, column=2, sticky="ew", padx=(0, 6)
        )

        ttk.Button(filters, text="Filtrar", command=self.refresh_grid).grid(row=1, column=3, padx=(0, 6))
        ttk.Button(filters, text="Limpar", command=self.clear_filters).grid(row=1, column=4, padx=(0, 6))
        ttk.Button(filters, text="Atualizar", command=self.refresh_grid).grid(row=1, column=5)
        ttk.Label(filters, textvariable=self.summary_var).grid(row=1, column=6, sticky="e")

        left = ttk.LabelFrame(root, text="Fila de Chamados", padding=10)
        left.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(10, 0))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        columns = ("protocol", "status", "priority", "machine_name", "title", "updated_at")
        self.tree = ttk.Treeview(left, columns=columns, show="headings")
        self.tree.heading("protocol", text="Protocolo")
        self.tree.heading("status", text="Status")
        self.tree.heading("priority", text="Prioridade")
        self.tree.heading("machine_name", text="Maquina")
        self.tree.heading("title", text="Titulo")
        self.tree.heading("updated_at", text="Atualizado em")

        self.tree.column("protocol", width=135, anchor="w")
        self.tree.column("status", width=150, anchor="center")
        self.tree.column("priority", width=95, anchor="center")
        self.tree.column("machine_name", width=130, anchor="center")
        self.tree.column("title", width=290, anchor="w")
        self.tree.column("updated_at", width=150, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        right = ttk.LabelFrame(root, text="Atendimento", padding=10)
        right.grid(row=2, column=1, sticky="nsew", pady=(10, 0))
        right.rowconfigure(5, weight=1)
        right.rowconfigure(7, weight=1)
        right.columnconfigure(1, weight=1)

        ttk.Label(right, text="Protocolo").grid(row=0, column=0, sticky="w")
        self.protocol_label = ttk.Label(right, text="-")
        self.protocol_label.grid(row=0, column=1, sticky="w")

        ttk.Label(right, text="Novo status").grid(row=1, column=0, sticky="w")
        ttk.Combobox(
            right, textvariable=self.edit_status_var, values=STATUSES, state="readonly", width=24
        ).grid(row=1, column=1, sticky="w", pady=(2, 8))

        ttk.Label(right, text="Atendente/Maquina").grid(row=2, column=0, sticky="w")
        ttk.Entry(right, textvariable=self.assigned_var).grid(row=2, column=1, sticky="ew", pady=(2, 8))

        ttk.Label(right, text="Notas TI").grid(row=3, column=0, sticky="nw")
        self.notes_text = tk.Text(right, height=7, wrap="word")
        self.notes_text.grid(row=3, column=1, sticky="nsew", pady=(2, 8))

        ttk.Button(right, text="Salvar atualizacao", command=self.save_update).grid(
            row=4, column=1, sticky="e", pady=(0, 8)
        )

        ttk.Label(right, text="Detalhes").grid(row=5, column=0, sticky="nw")
        self.details_text = tk.Text(right, height=10, wrap="word", state="disabled")
        self.details_text.grid(row=5, column=1, sticky="nsew")

        ttk.Label(right, text="Historico").grid(row=6, column=0, sticky="nw", pady=(8, 0))
        self.history_text = tk.Text(right, height=9, wrap="word", state="disabled")
        self.history_text.grid(row=7, column=1, sticky="nsew", pady=(8, 0))

    def clear_filters(self) -> None:
        self.status_filter_var.set("TODOS")
        self.priority_filter_var.set("TODAS")
        self.search_var.set("")
        self.refresh_grid()

    def refresh_grid(self) -> None:
        try:
            rows = self.db.list_tickets(
                status=self.status_filter_var.get(),
                priority=self.priority_filter_var.get(),
                search=self.search_var.get().strip(),
            )
            counts = self.db.status_counts()
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao carregar fila.\n{exc}")
            return

        self.summary_var.set(
            " | ".join(
                [
                    f"Total: {counts.get('TOTAL', 0)}",
                    f"Abertos: {counts.get('ABERTO', 0)}",
                    f"Em atendimento: {counts.get('EM_ATENDIMENTO', 0)}",
                    f"Aguardando usuario: {counts.get('AGUARDANDO_USUARIO', 0)}",
                ]
            )
        )

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
                    row["machine_name"],
                    row["title"],
                    row["updated_at"],
                ),
            )

    def on_tree_select(self, _event: object) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        protocol = self.tree.item(selected[0], "values")[0]
        self.load_ticket(protocol)

    def load_ticket(self, protocol: str) -> None:
        ticket = self.db.get_ticket(protocol)
        events = self.db.list_events(protocol)
        if ticket is None:
            messagebox.showwarning("Aviso", "Chamado nao encontrado.")
            return

        self.selected_protocol = protocol
        self.protocol_label.configure(text=protocol)
        self.edit_status_var.set(ticket["status"])
        self.assigned_var.set(ticket["assigned_machine"] or self.current_machine_name)

        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", ticket["ti_notes"] or "")

        detail_lines = [
            f"Protocolo: {ticket['protocol']}",
            f"Status: {ticket['status']}",
            f"Prioridade: {ticket['priority']}",
            f"Categoria: {ticket['category']}",
            f"Solicitante: {ticket['requester_name'] or '-'}",
            f"Maquina origem: {ticket['machine_name']} ({ticket['machine_id']})",
            f"Aberto em: {ticket['created_at']}",
            f"Atualizado em: {ticket['updated_at']}",
            f"Encerrado em: {ticket['closed_at'] or '-'}",
            "",
            f"Titulo: {ticket['title']}",
            "",
            "Descricao:",
            ticket["description"],
        ]
        self._set_readonly_text(self.details_text, "\n".join(detail_lines))

        history_lines = []
        for evt in events:
            history_lines.append(
                f"{evt['created_at']} | {evt['event_type']} | {evt['event_desc']}"
            )
        self._set_readonly_text(self.history_text, "\n".join(history_lines))

    def save_update(self) -> None:
        if not self.selected_protocol:
            messagebox.showwarning("Validacao", "Selecione um chamado na fila.")
            return

        new_status = self.edit_status_var.get().strip()
        assigned = self.assigned_var.get().strip()
        notes = self.notes_text.get("1.0", tk.END).strip()

        if new_status not in STATUSES:
            messagebox.showwarning("Validacao", "Selecione um status valido.")
            return
        if new_status in OPEN_STATUSES and not assigned:
            messagebox.showwarning("Validacao", "Informe o atendente/maquina responsavel.")
            return

        try:
            self.db.update_ticket(
                protocol=self.selected_protocol,
                new_status=new_status,
                assigned_machine=assigned,
                ti_notes=notes,
                event_machine=self.current_machine_name,
            )
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao atualizar chamado.\n{exc}")
            return

        self.refresh_grid()
        self.load_ticket(self.selected_protocol)
        messagebox.showinfo("Sucesso", "Chamado atualizado.")

    def _set_readonly_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _auto_refresh(self) -> None:
        selected = self.selected_protocol
        self.refresh_grid()
        if selected:
            ticket = self.db.get_ticket(selected)
            if ticket is not None:
                self.load_ticket(selected)
        self.after(12000, self._auto_refresh)


def main() -> None:
    app = TIApp()
    app.mainloop()


if __name__ == "__main__":
    main()
