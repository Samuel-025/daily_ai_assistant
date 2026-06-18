"""Tests for TaskCRUD (utils/task_manager.py)"""

import json
import pytest
from pathlib import Path
from utils.task_manager import TaskCRUD


@pytest.fixture
def crud(tmp_path: Path) -> TaskCRUD:
    """Fresh TaskCRUD instance backed by a temp directory."""
    return TaskCRUD(tmp_path)


# ── add ─────────────────────────────────────────────────────────────────

class TestAdd:
    def test_add_single_task_persists(self, crud, tmp_path):
        crud.add("Buy milk")
        data = json.loads((tmp_path / "tasks" / "today_tasks.json").read_text())
        assert "Buy milk" in data["tasks"]

    def test_add_returns_confirmation(self, crud):
        result = crud.add("Write tests")
        assert "Write tests" in result
        assert "#1" in result

    def test_add_multiple_tasks_increments_number(self, crud):
        crud.add("Task A")
        result = crud.add("Task B")
        assert "#2" in result

    def test_add_empty_string_rejected(self, crud):
        result = crud.add("")
        # Should return an error/warning, not add a blank task
        data = json.loads((crud.tasks_file).read_text()) if crud.tasks_file.exists() else {"tasks": []}
        assert "" not in data.get("tasks", [])

    def test_add_whitespace_only_rejected(self, crud):
        result = crud.add("   ")
        assert result  # returns some feedback
        data = json.loads(crud.tasks_file.read_text()) if crud.tasks_file.exists() else {"tasks": []}
        assert all(t.strip() for t in data.get("tasks", []))


# ── complete ──────────────────────────────────────────────────────────

class TestComplete:
    def test_complete_moves_task_to_done(self, crud, tmp_path):
        crud.add("Send email")
        crud.complete(1)
        data = json.loads((tmp_path / "tasks" / "today_tasks.json").read_text())
        assert "Send email" not in data["tasks"]
        assert "Send email" in data["completed"]

    def test_complete_returns_confirmation(self, crud):
        crud.add("Fix bug")
        result = crud.complete(1)
        assert "Fix bug" in result

    def test_complete_invalid_index_returns_error(self, crud):
        crud.add("One task")
        result = crud.complete(99)
        assert result  # some error message
        # Task should still be active
        data = json.loads(crud.tasks_file.read_text())
        assert "One task" in data["tasks"]

    def test_complete_zero_index_returns_error(self, crud):
        crud.add("Zero test")
        result = crud.complete(0)
        assert result
        data = json.loads(crud.tasks_file.read_text())
        assert "Zero test" in data["tasks"]  # untouched

    def test_complete_correct_task_when_multiple(self, crud, tmp_path):
        crud.add("Alpha")
        crud.add("Beta")
        crud.add("Gamma")
        crud.complete(2)  # Beta
        data = json.loads((tmp_path / "tasks" / "today_tasks.json").read_text())
        assert "Beta" not in data["tasks"]
        assert "Alpha" in data["tasks"]
        assert "Gamma" in data["tasks"]
        assert "Beta" in data["completed"]


# ── delete ─────────────────────────────────────────────────────────────

class TestDelete:
    def test_delete_removes_task_permanently(self, crud, tmp_path):
        crud.add("Temp task")
        crud.delete(1)
        data = json.loads((tmp_path / "tasks" / "today_tasks.json").read_text())
        assert "Temp task" not in data["tasks"]
        assert "Temp task" not in data["completed"]

    def test_delete_returns_confirmation(self, crud):
        crud.add("Delete me")
        result = crud.delete(1)
        assert "Delete me" in result

    def test_delete_invalid_index_returns_error(self, crud):
        crud.add("Safe task")
        result = crud.delete(5)
        assert result
        data = json.loads(crud.tasks_file.read_text())
        assert "Safe task" in data["tasks"]

    def test_delete_middle_task_preserves_others(self, crud, tmp_path):
        crud.add("First")
        crud.add("Second")
        crud.add("Third")
        crud.delete(2)
        data = json.loads((tmp_path / "tasks" / "today_tasks.json").read_text())
        assert "Second" not in data["tasks"]
        assert "First" in data["tasks"]
        assert "Third" in data["tasks"]


# ── clear_completed ────────────────────────────────────────────────

class TestClearCompleted:
    def test_clear_completed_empties_done_list(self, crud, tmp_path):
        crud.add("Task 1")
        crud.add("Task 2")
        crud.complete(1)
        crud.complete(1)  # now Task 2 is #1
        crud.clear_completed()
        data = json.loads((tmp_path / "tasks" / "today_tasks.json").read_text())
        assert data["completed"] == []

    def test_clear_completed_preserves_active(self, crud, tmp_path):
        crud.add("Keep me")
        crud.add("Done me")
        crud.complete(2)
        crud.clear_completed()
        data = json.loads((tmp_path / "tasks" / "today_tasks.json").read_text())
        assert "Keep me" in data["tasks"]

    def test_clear_completed_when_empty_is_safe(self, crud):
        result = crud.clear_completed()
        assert result  # some message, no crash


# ── clear_all ──────────────────────────────────────────────────────────────

class TestClearAll:
    def test_clear_all_wipes_everything(self, crud, tmp_path):
        crud.add("A")
        crud.add("B")
        crud.complete(1)
        crud.clear_all()
        data = json.loads((tmp_path / "tasks" / "today_tasks.json").read_text())
        assert data["tasks"] == []
        assert data["completed"] == []

    def test_clear_all_returns_confirmation(self, crud):
        crud.add("Will be wiped")
        result = crud.clear_all()
        assert result


# ── list_tasks ───────────────────────────────────────────────────────────

class TestListTasks:
    def test_list_tasks_shows_all_active(self, crud):
        crud.add("Alpha")
        crud.add("Beta")
        result = crud.list_tasks()
        assert "Alpha" in result
        assert "Beta" in result

    def test_list_tasks_shows_completed(self, crud):
        crud.add("Done task")
        crud.complete(1)
        result = crud.list_tasks()
        assert "Done task" in result

    def test_list_tasks_empty_state(self, crud):
        result = crud.list_tasks()
        assert result  # should return some message, not crash


# ── summary ─────────────────────────────────────────────────────────────

class TestSummary:
    def test_summary_reflects_counts(self, crud):
        crud.add("One")
        crud.add("Two")
        crud.complete(1)
        result = crud.summary()
        assert "1" in result   # 1 active remaining
        assert "1" in result   # 1 completed

    def test_summary_on_empty(self, crud):
        result = crud.summary()
        assert result


# ── persistence across instances ────────────────────────────────────

class TestPersistence:
    def test_data_persists_across_crud_instances(self, tmp_path):
        c1 = TaskCRUD(tmp_path)
        c1.add("Persistent task")
        c2 = TaskCRUD(tmp_path)  # new instance, same dir
        result = c2.list_tasks()
        assert "Persistent task" in result

    def test_completions_persist_across_instances(self, tmp_path):
        c1 = TaskCRUD(tmp_path)
        c1.add("Complete me")
        c1.complete(1)
        c2 = TaskCRUD(tmp_path)
        data = json.loads((tmp_path / "tasks" / "today_tasks.json").read_text())
        assert "Complete me" in data["completed"]
        assert "Complete me" not in data["tasks"]
