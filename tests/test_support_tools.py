import json

from app.tools.support_tools import SupportToolService


def test_create_followup_note_updates_ticket(tmp_path) -> None:
    tickets = [
        {
            "ticket_id": "INC-1",
            "status": "open",
            "follow_up_notes": [],
        }
    ]
    errors = [{"error_code": "A1", "meaning": "x", "recommended_action": "y"}]
    (tmp_path / "tickets.json").write_text(json.dumps(tickets), encoding="utf-8")
    (tmp_path / "error_codes.json").write_text(json.dumps(errors), encoding="utf-8")

    service = SupportToolService(data_dir=tmp_path)
    result = service.create_followup_note("INC-1", "Please verify the device serial number.")

    assert result["status"] == "note_created"
    saved = json.loads((tmp_path / "tickets.json").read_text(encoding="utf-8"))
    assert len(saved[0]["follow_up_notes"]) == 1
