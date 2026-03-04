from __future__ import annotations

from dataclasses import dataclass


STATUSES = [
    "ABERTO",
    "EM_ATENDIMENTO",
    "AGUARDANDO_USUARIO",
    "RESOLVIDO",
    "CANCELADO",
]

OPEN_STATUSES = {"ABERTO", "EM_ATENDIMENTO", "AGUARDANDO_USUARIO"}

PRIORITIES = ["BAIXA", "MEDIA", "ALTA", "CRITICA"]

CATEGORIES = [
    "Hardware",
    "Software",
    "Acesso",
    "Rede",
    "Impressora",
    "Outros",
]


@dataclass(slots=True)
class TicketUpdate:
    status: str
    assigned_machine: str
    ti_notes: str

