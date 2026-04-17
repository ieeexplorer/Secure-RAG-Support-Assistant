from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import PROJECT_ROOT


class SupportToolService:
    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or (PROJECT_ROOT / "data" / "mock")
        self._ticket_path = self._data_dir / "tickets.json"
        self._error_path = self._data_dir / "error_codes.json"
        self.allowed_tools = {
            "search_ticket_status",
            "lookup_error_code",
            "create_followup_note",
        }

    def _load_json(self, path: Path) -> list[dict[str, Any]]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: list[dict[str, Any]]) -> None:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def list_tickets(self) -> list[dict[str, Any]]:
        return self._load_json(self._ticket_path)

    def list_error_codes(self) -> list[dict[str, Any]]:
        return self._load_json(self._error_path)

    def search_ticket_status(self, ticket_id: str) -> dict[str, Any]:
        self._enforce_tool("search_ticket_status")
        tickets = self.list_tickets()
        ticket = next((row for row in tickets if row["ticket_id"] == ticket_id), None)
        if ticket is None:
            raise ValueError(f"Unknown ticket_id: {ticket_id}")
        return ticket

    def lookup_error_code(self, error_code: str) -> dict[str, Any]:
        self._enforce_tool("lookup_error_code")
        errors = self.list_error_codes()
        record = next((row for row in errors if row["error_code"] == error_code.upper()), None)
        if record is None:
            raise ValueError(f"Unknown error_code: {error_code}")
        return record

    def create_followup_note(self, ticket_id: str, note: str, author: str = "assistant") -> dict[str, Any]:
        self._enforce_tool("create_followup_note")
        if len(note.strip()) < 5:
            raise ValueError("Note is too short")

        tickets = self._load_json(self._ticket_path)
        ticket = next((row for row in tickets if row["ticket_id"] == ticket_id), None)
        if ticket is None:
            raise ValueError(f"Unknown ticket_id: {ticket_id}")

        notes = ticket.setdefault("follow_up_notes", [])
        notes.append(
            {
                "author": author,
                "note": note.strip(),
                "created_at": datetime.now(UTC).isoformat(),
            }
        )
        self._write_json(self._ticket_path, tickets)
        return {"ticket_id": ticket_id, "status": "note_created", "note_count": len(notes)}

    def _enforce_tool(self, tool_name: str) -> None:
        if tool_name not in self.allowed_tools:
            raise PermissionError(f"Tool not allowlisted: {tool_name}")
