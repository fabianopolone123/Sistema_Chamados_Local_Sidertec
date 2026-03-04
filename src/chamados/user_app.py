from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .config import (
    get_database_path,
    get_update_check_interval_seconds,
    get_update_manifest_path,
)
from .database import Database
from .machine import machine_id, machine_name
from .models import CATEGORIES, PRIORITIES
from .update_checker import UpdateChecker
from .version import __version__


class UserApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Chamados Usuario")
        self.geometry("980x640")
        self.minsize(860, 560)

        self.db = Database(get_database_path())
        self.current_machine_id = machine_id()
        self.current_machine_name = machine_name()
        self.update_checker = self._build_update_checker()
        self.status_var = tk.StringVar(
            value=(
                f"Maquina: {self.current_machine_name} ({self.current_machine_id}) | "
                f"Versao: {__version__}"
            )
        )

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.refresh_tickets()
        self.after(15000, self._auto_refresh)
        if self.update_checker is not None:
            self.after(8000, self._auto_check_updates)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        root.rowconfigure(1, weight=1)
        root.rowconfigure(2, weight=1)
        root.columnconfigure(0, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Abrir novo chamado", command=self.open_new_ticket_window).grid(
            row=0, column=1, sticky="e", padx=(8, 0)
        )
        ttk.Button(header, text="Verificar atualizacao", command=self.check_updates_manually).grid(
            row=0, column=2, sticky="e", padx=(8, 0)
        )

        list_frame = ttk.LabelFrame(root, text="Meus chamados (por maquina)", padding=10)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = ("protocol", "status", "priority", "title", "updated_at")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("protocol", text="Protocolo")
        self.tree.heading("status", text="Status")
        self.tree.heading("priority", text="Prioridade")
        self.tree.heading("title", text="Titulo")
        self.tree.heading("updated_at", text="Atualizado em")
        self.tree.column("protocol", width=135, anchor="w")
        self.tree.column("status", width=150, anchor="center")
        self.tree.column("priority", width=100, anchor="center")
        self.tree.column("title", width=420, anchor="w")
        self.tree.column("updated_at", width=170, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        details_frame = ttk.LabelFrame(root, text="Detalhes", padding=10)
        details_frame.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        details_frame.rowconfigure(0, weight=1)
        details_frame.columnconfigure(0, weight=1)

        self.details = tk.Text(details_frame, height=12, wrap="word", state="disabled")
        self.details.grid(row=0, column=0, sticky="nsew")

    def open_new_ticket_window(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Novo chamado")
        dialog.geometry("560x470")
        dialog.minsize(520, 430)
        dialog.transient(self)
        dialog.grab_set()

        title_var = tk.StringVar()
        category_var = tk.StringVar(value=CATEGORIES[0])
        priority_var = tk.StringVar(value=PRIORITIES[1])

        form = ttk.Frame(dialog, padding=12)
        form.pack(fill="both", expand=True)
        form.columnconfigure(0, weight=1)
        form.rowconfigure(4, weight=1)

        ttk.Label(form, text="Titulo").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=title_var).grid(row=1, column=0, sticky="ew", pady=(2, 8))

        selectors = ttk.Frame(form)
        selectors.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        selectors.columnconfigure(0, weight=1)
        selectors.columnconfigure(1, weight=1)

        ttk.Label(selectors, text="Categoria").grid(row=0, column=0, sticky="w")
        ttk.Label(selectors, text="Prioridade").grid(row=0, column=1, sticky="w")
        ttk.Combobox(
            selectors, textvariable=category_var, values=CATEGORIES, state="readonly"
        ).grid(row=1, column=0, sticky="ew", padx=(0, 6))
        ttk.Combobox(
            selectors, textvariable=priority_var, values=PRIORITIES, state="readonly"
        ).grid(row=1, column=1, sticky="ew")

        ttk.Label(form, text="Descricao").grid(row=3, column=0, sticky="w")
        description_text = tk.Text(form, height=12, wrap="word")
        description_text.grid(row=4, column=0, sticky="nsew", pady=(2, 10))

        actions = ttk.Frame(form)
        actions.grid(row=5, column=0, sticky="e")

        def save_ticket() -> None:
            title = title_var.get().strip()
            desc = description_text.get("1.0", tk.END).strip()
            category = category_var.get().strip()
            priority = priority_var.get().strip()

            if not title:
                messagebox.showwarning("Validacao", "Informe um titulo para o chamado.", parent=dialog)
                return
            if len(desc) < 10:
                messagebox.showwarning(
                    "Validacao",
                    "A descricao deve ter pelo menos 10 caracteres.",
                    parent=dialog,
                )
                return

            try:
                protocol = self.db.create_ticket(
                    requester_name="",
                    machine_name=self.current_machine_name,
                    machine_id=self.current_machine_id,
                    title=title,
                    description=desc,
                    category=category,
                    priority=priority,
                )
            except Exception as exc:
                messagebox.showerror("Erro", f"Falha ao abrir chamado.\n{exc}", parent=dialog)
                return

            dialog.destroy()
            self.refresh_tickets()
            messagebox.showinfo("Sucesso", f"Chamado aberto com protocolo {protocol}.")

        ttk.Button(actions, text="Cancelar", command=dialog.destroy).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(actions, text="Abrir chamado", command=save_ticket).grid(row=0, column=1)

    def refresh_tickets(self) -> None:
        selected = self.tree.selection()
        selected_protocol = ""
        if selected:
            selected_protocol = self.tree.item(selected[0], "values")[0]

        try:
            rows = self.db.list_tickets_by_machine(self.current_machine_id)
        except Exception as exc:
            messagebox.showerror("Erro", f"Falha ao carregar chamados.\n{exc}")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        selected_item = None
        for row in rows:
            item = self.tree.insert(
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
            if row["protocol"] == selected_protocol:
                selected_item = item

        if selected_item:
            self.tree.selection_set(selected_item)
            self.tree.focus(selected_item)
            self.on_tree_select(None)
        elif rows:
            first_item = self.tree.get_children()[0]
            self.tree.selection_set(first_item)
            self.tree.focus(first_item)
            self.on_tree_select(None)
        else:
            self._set_details("Nenhum chamado encontrado para esta maquina.")

    def on_tree_select(self, _event: object | None) -> None:
        selected = self.tree.selection()
        if not selected:
            self._set_details("Selecione um chamado para ver os detalhes.")
            return

        protocol = self.tree.item(selected[0], "values")[0]
        ticket = self.db.get_ticket(protocol)
        events = self.db.list_events(protocol, limit=8)
        if ticket is None:
            self._set_details("Chamado nao encontrado.")
            return

        lines = [
            f"Protocolo: {ticket['protocol']}",
            f"Status: {ticket['status']}",
            f"Prioridade: {ticket['priority']}",
            f"Categoria: {ticket['category']}",
            f"Aberto em: {ticket['created_at']}",
            f"Atualizado em: {ticket['updated_at']}",
            f"Encerrado em: {ticket['closed_at'] or '-'}",
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
            lines.append(f"- {evt['created_at']} | {evt['event_type']} | {evt['event_desc']}")
        self._set_details("\n".join(lines))

    def _set_details(self, value: str) -> None:
        self.details.configure(state="normal")
        self.details.delete("1.0", tk.END)
        self.details.insert("1.0", value)
        self.details.configure(state="disabled")

    def _auto_refresh(self) -> None:
        self.refresh_tickets()
        self.after(15000, self._auto_refresh)

    def _build_update_checker(self) -> UpdateChecker | None:
        manifest_path = get_update_manifest_path()
        if manifest_path is None:
            return None

        interval = get_update_check_interval_seconds(default=1800)
        return UpdateChecker(
            current_version=__version__,
            manifest_path=manifest_path,
            interval_seconds=interval,
        )

    def _auto_check_updates(self) -> None:
        self._check_updates(interactive=False)
        if self.update_checker is not None:
            self.after(self.update_checker.interval_seconds * 1000, self._auto_check_updates)

    def check_updates_manually(self) -> None:
        self._check_updates(interactive=True)

    def _check_updates(self, interactive: bool) -> None:
        if self.update_checker is None:
            if interactive:
                messagebox.showinfo(
                    "Atualizacao",
                    "Atualizacao automatica nao configurada.\n"
                    "Defina 'update_manifest_path' no config.json.",
                )
            return

        info = self.update_checker.get_available_update()
        if info is None:
            if interactive:
                messagebox.showinfo("Atualizacao", "Voce ja esta na versao mais recente.")
            return

        if not interactive and not self.update_checker.should_prompt(info.latest_version):
            return

        details = (
            f"Versao atual: {__version__}\n"
            f"Nova versao: {info.latest_version}\n"
            f"Instalador: {info.installer_path}\n"
        )
        if info.notes:
            details += f"\nNotas:\n{info.notes}\n"
        details += "\nDeseja abrir o instalador agora?"

        should_update = messagebox.askyesno("Atualizacao disponivel", details)
        if not should_update:
            return

        if not self.update_checker.run_installer(info.installer_path):
            messagebox.showerror(
                "Atualizacao",
                "Nao foi possivel abrir o instalador.\n"
                "Verifique se o arquivo existe e se voce tem permissao de acesso.",
            )


def main() -> None:
    app = UserApp()
    app.mainloop()


if __name__ == "__main__":
    main()
