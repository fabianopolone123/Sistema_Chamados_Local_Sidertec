from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import OPEN_STATUSES


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Database:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    protocol TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    closed_at TEXT,
                    requester_name TEXT,
                    machine_name TEXT NOT NULL,
                    machine_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assigned_machine TEXT,
                    ti_notes TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS ticket_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    event_desc TEXT NOT NULL,
                    event_machine TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
                CREATE INDEX IF NOT EXISTS idx_tickets_machine ON tickets(machine_id);
                CREATE INDEX IF NOT EXISTS idx_tickets_updated_at ON tickets(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_ticket_events_ticket ON ticket_events(ticket_id);
                """
            )

    def _new_protocol(self) -> str:
        date_part = datetime.now().strftime("%Y%m%d")
        rand_part = secrets.randbelow(9000) + 1000
        return f"CHM-{date_part}-{rand_part}"

    def create_ticket(
        self,
        requester_name: str,
        machine_name: str,
        machine_id: str,
        title: str,
        description: str,
        category: str,
        priority: str,
    ) -> str:
        requester_name = requester_name.strip()
        title = title.strip()
        description = description.strip()
        category = category.strip()
        priority = priority.strip()

        if not title:
            raise ValueError("Titulo e obrigatorio.")
        if len(description) < 10:
            raise ValueError("Descricao precisa ter pelo menos 10 caracteres.")

        for _ in range(30):
            protocol = self._new_protocol()
            timestamp = now_str()

            try:
                with self._connect() as conn:
                    cursor = conn.execute(
                        """
                        INSERT INTO tickets (
                            protocol, created_at, updated_at, closed_at, requester_name,
                            machine_name, machine_id, title, description, category,
                            priority, status, assigned_machine, ti_notes
                        ) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, 'ABERTO', '', '')
                        """,
                        (
                            protocol,
                            timestamp,
                            timestamp,
                            requester_name,
                            machine_name,
                            machine_id,
                            title,
                            description,
                            category,
                            priority,
                        ),
                    )
                    ticket_id = cursor.lastrowid
                    conn.execute(
                        """
                        INSERT INTO ticket_events (
                            ticket_id, event_type, event_desc, event_machine, created_at
                        ) VALUES (?, 'CREATED', 'Chamado aberto.', ?, ?)
                        """,
                        (ticket_id, machine_name, timestamp),
                    )
                return protocol
            except sqlite3.IntegrityError:
                continue

        raise RuntimeError("Nao foi possivel gerar protocolo unico.")

    def list_tickets_by_machine(self, machine_id: str, limit: int = 300) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT protocol, created_at, updated_at, status, priority, title, category, closed_at
                FROM tickets
                WHERE machine_id = ?
                ORDER BY datetime(created_at) DESC
                LIMIT ?
                """,
                (machine_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_tickets(
        self,
        status: str | None = None,
        priority: str | None = None,
        search: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        where_parts: list[str] = []
        params: list[Any] = []

        if status and status != "TODOS":
            where_parts.append("status = ?")
            params.append(status)
        if priority and priority != "TODAS":
            where_parts.append("priority = ?")
            params.append(priority)
        if search:
            where_parts.append("(protocol LIKE ? OR title LIKE ? OR machine_name LIKE ?)")
            token = f"%{search.strip()}%"
            params.extend([token, token, token])

        where_sql = ""
        if where_parts:
            where_sql = "WHERE " + " AND ".join(where_parts)

        params.append(limit)
        sql = f"""
            SELECT protocol, created_at, updated_at, status, priority, title, machine_name, category
            FROM tickets
            {where_sql}
            ORDER BY
                CASE WHEN status IN ('ABERTO', 'EM_ATENDIMENTO', 'AGUARDANDO_USUARIO') THEN 0 ELSE 1 END,
                datetime(updated_at) DESC
            LIMIT ?
        """

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def get_ticket(self, protocol: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM tickets
                WHERE protocol = ?
                """,
                (protocol,),
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def update_ticket(
        self,
        protocol: str,
        new_status: str,
        assigned_machine: str,
        ti_notes: str,
        event_machine: str,
    ) -> None:
        ticket = self.get_ticket(protocol)
        if ticket is None:
            raise ValueError("Chamado nao encontrado.")

        assigned_machine = assigned_machine.strip()
        ti_notes = ti_notes.strip()
        new_status = new_status.strip()
        if not new_status:
            raise ValueError("Status invalido.")

        timestamp = now_str()
        closed_at = timestamp if new_status not in OPEN_STATUSES else None
        old_status = ticket["status"]

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE tickets
                SET
                    status = ?,
                    assigned_machine = ?,
                    ti_notes = ?,
                    updated_at = ?,
                    closed_at = ?
                WHERE protocol = ?
                """,
                (new_status, assigned_machine, ti_notes, timestamp, closed_at, protocol),
            )

            event_desc = (
                f"Status alterado de {old_status} para {new_status}. "
                f"Responsavel: {assigned_machine or 'Nao informado'}."
            )
            conn.execute(
                """
                INSERT INTO ticket_events (
                    ticket_id, event_type, event_desc, event_machine, created_at
                ) VALUES (?, 'STATUS_CHANGED', ?, ?, ?)
                """,
                (ticket["id"], event_desc, event_machine, timestamp),
            )

    def list_events(self, protocol: str, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT e.event_type, e.event_desc, e.event_machine, e.created_at
                FROM ticket_events e
                INNER JOIN tickets t ON t.id = e.ticket_id
                WHERE t.protocol = ?
                ORDER BY datetime(e.created_at) DESC
                LIMIT ?
                """,
                (protocol, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def status_counts(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT status, COUNT(*) AS qty
                FROM tickets
                GROUP BY status
                """
            ).fetchall()
        result = {row["status"]: row["qty"] for row in rows}
        result["TOTAL"] = sum(result.values())
        return result

