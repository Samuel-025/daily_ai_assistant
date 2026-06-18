"""Tests for HabitCheckIn (utils/habit_checkin.py)"""

import json
import pytest
from datetime import date
from pathlib import Path
from utils.habit_checkin import HabitCheckIn


TODAY = date.today().isoformat()
OTHER_DAY = "2000-01-01"


# ── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def ci(tmp_path: Path) -> HabitCheckIn:
    """Fresh HabitCheckIn backed by a temp dir with 3 sample habits."""
    habits_dir = tmp_path / "habits"
    habits_dir.mkdir()
    data = {
        "habits": [
            {"name": "Exercise",  "streak": 5,  "target": 30},
            {"name": "Read",      "streak": 10, "target": 21},
            {"name": "Meditate",  "streak": 0,  "target": 21},
        ]
    }
    (habits_dir / "current_habits.json").write_text(json.dumps(data))
    return HabitCheckIn(tmp_path)


@pytest.fixture
def ci_empty(tmp_path: Path) -> HabitCheckIn:
    """HabitCheckIn with zero habits."""
    (tmp_path / "habits").mkdir()
    (tmp_path / "habits" / "current_habits.json").write_text(json.dumps({"habits": []}))
    return HabitCheckIn(tmp_path)


@pytest.fixture
def ci_partial(tmp_path: Path) -> HabitCheckIn:
    """HabitCheckIn where habit 0 is already checked in today."""
    habits_dir = tmp_path / "habits"
    habits_dir.mkdir()
    data = {
        "habits": [
            {"name": "Exercise",  "streak": 5, "target": 30, "last_checked": TODAY},
            {"name": "Read",      "streak": 3, "target": 21},
        ]
    }
    (habits_dir / "current_habits.json").write_text(json.dumps(data))
    return HabitCheckIn(tmp_path)


# ── today_status ──────────────────────────────────────────────────────

class TestTodayStatus:
    def test_returns_all_habits(self, ci):
        status = ci.today_status()
        assert len(status) == 3

    def test_fields_present(self, ci):
        status = ci.today_status()
        for h in status:
            assert "name"   in h
            assert "streak" in h
            assert "target" in h
            assert "done"   in h

    def test_not_done_by_default(self, ci):
        status = ci.today_status()
        assert all(not h["done"] for h in status)

    def test_already_checked_shows_done(self, ci_partial):
        status = ci_partial.today_status()
        assert status[0]["done"] is True
        assert status[1]["done"] is False

    def test_empty_habits_returns_empty_list(self, ci_empty):
        assert ci_empty.today_status() == []


# ── already_checked_in ──────────────────────────────────────────────

class TestAlreadyCheckedIn:
    def test_false_when_not_checked_in(self, ci):
        assert ci.already_checked_in() is False

    def test_true_when_all_checked_in(self, ci):
        ci.check_in([0, 1, 2])
        assert ci.already_checked_in() is True

    def test_false_when_only_partial(self, ci_partial):
        # only 1 of 2 habits checked in
        assert ci_partial.already_checked_in() is False


# ── check_in ─────────────────────────────────────────────────────────────

class TestCheckIn:
    def test_check_in_increments_streak(self, ci, tmp_path):
        ci.check_in([0])  # Exercise had streak=5
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert data["habits"][0]["streak"] == 6

    def test_check_in_sets_last_checked(self, ci, tmp_path):
        ci.check_in([1])  # Read
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert data["habits"][1]["last_checked"] == TODAY

    def test_check_in_multiple_habits(self, ci, tmp_path):
        ci.check_in([0, 2])  # Exercise + Meditate
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert data["habits"][0]["streak"] == 6
        assert data["habits"][2]["streak"] == 1
        assert data["habits"][1]["streak"] == 10  # Read untouched

    def test_check_in_all(self, ci, tmp_path):
        ci.check_in([0, 1, 2])
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert all(h.get("last_checked") == TODAY for h in data["habits"])

    def test_check_in_none_changes_nothing(self, ci, tmp_path):
        ci.check_in([])
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert data["habits"][0]["streak"] == 5
        assert data["habits"][1]["streak"] == 10
        assert data["habits"][2]["streak"] == 0

    def test_check_in_idempotent_same_day(self, ci, tmp_path):
        """Calling check_in twice on the same day must NOT double-increment."""
        ci.check_in([0])
        ci.check_in([0])  # second call same day
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert data["habits"][0]["streak"] == 6  # still 6, not 7

    def test_check_in_returns_summary_string(self, ci):
        result = ci.check_in([0, 1])
        assert "Exercise" in result
        assert "Read" in result

    def test_check_in_strict_resets_skipped(self, ci, tmp_path):
        ci.check_in([0], strict=True)  # skip Read (1) and Meditate (2)
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert data["habits"][1]["streak"] == 0  # Read reset
        assert data["habits"][2]["streak"] == 0  # Meditate unchanged (was 0)

    def test_check_in_non_strict_preserves_skipped_streak(self, ci, tmp_path):
        ci.check_in([0], strict=False)  # Read skipped
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert data["habits"][1]["streak"] == 10  # Read streak preserved


# ── add_habit ────────────────────────────────────────────────────────────

class TestAddHabit:
    def test_add_new_habit_appears_in_list(self, ci, tmp_path):
        ci.add_habit("Journaling", target=14)
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        names = [h["name"] for h in data["habits"]]
        assert "Journaling" in names

    def test_add_habit_sets_correct_target(self, ci, tmp_path):
        ci.add_habit("Walk 5000 steps", target=60)
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        habit = next(h for h in data["habits"] if h["name"] == "Walk 5000 steps")
        assert habit["target"] == 60

    def test_add_habit_starts_with_zero_streak(self, ci, tmp_path):
        ci.add_habit("Cold shower")
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        habit = next(h for h in data["habits"] if h["name"] == "Cold shower")
        assert habit["streak"] == 0

    def test_add_duplicate_habit_rejected(self, ci):
        result = ci.add_habit("Exercise")  # already exists
        assert "already" in result.lower() or "exist" in result.lower()

    def test_add_duplicate_case_insensitive(self, ci):
        result = ci.add_habit("exercise")  # case-insensitive match
        assert "already" in result.lower() or "exist" in result.lower()

    def test_add_habit_returns_confirmation(self, ci):
        result = ci.add_habit("New habit")
        assert "New habit" in result

    def test_add_to_empty_list(self, ci_empty, tmp_path):
        ci_empty.add_habit("First habit")
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert len(data["habits"]) == 1
        assert data["habits"][0]["name"] == "First habit"


# ── remove_habit ─────────────────────────────────────────────────────────

class TestRemoveHabit:
    def test_remove_first_habit(self, ci, tmp_path):
        ci.remove_habit(1)  # Exercise
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        names = [h["name"] for h in data["habits"]]
        assert "Exercise" not in names
        assert len(names) == 2

    def test_remove_middle_habit_preserves_others(self, ci, tmp_path):
        ci.remove_habit(2)  # Read
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        names = [h["name"] for h in data["habits"]]
        assert "Read" not in names
        assert "Exercise" in names
        assert "Meditate" in names

    def test_remove_invalid_index_returns_error(self, ci):
        result = ci.remove_habit(99)
        assert result
        data = json.loads(ci.file.read_text())
        assert len(data["habits"]) == 3  # unchanged

    def test_remove_zero_index_returns_error(self, ci):
        result = ci.remove_habit(0)
        assert result
        data = json.loads(ci.file.read_text())
        assert len(data["habits"]) == 3

    def test_remove_returns_confirmation(self, ci):
        result = ci.remove_habit(1)
        assert "Exercise" in result


# ── reset_streak ─────────────────────────────────────────────────────────

class TestResetStreak:
    def test_reset_streak_zeroes_value(self, ci, tmp_path):
        ci.reset_streak(2)  # Read has streak=10
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert data["habits"][1]["streak"] == 0

    def test_reset_clears_last_checked(self, ci, tmp_path):
        ci.check_in([0])   # mark Exercise as done today
        ci.reset_streak(1) # reset it
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert "last_checked" not in data["habits"][0]

    def test_reset_invalid_index_returns_error(self, ci):
        result = ci.reset_streak(99)
        assert result

    def test_reset_other_habits_untouched(self, ci, tmp_path):
        ci.reset_streak(2)  # Read
        data = json.loads((tmp_path / "habits" / "current_habits.json").read_text())
        assert data["habits"][0]["streak"] == 5   # Exercise untouched
        assert data["habits"][2]["streak"] == 0   # Meditate untouched


# ── summary_line ────────────────────────────────────────────────────────

class TestSummaryLine:
    def test_summary_shows_fraction(self, ci):
        result = ci.summary_line()
        assert "/" in result  # e.g. "0/3"

    def test_summary_shows_best_streak(self, ci):
        result = ci.summary_line()
        assert "Read" in result or "10" in result   # best streak is Read@10

    def test_summary_after_checkin_updates_count(self, ci):
        ci.check_in([0, 1])
        result = ci.summary_line()
        assert "2/3" in result

    def test_summary_empty_habits(self, ci_empty):
        result = ci_empty.summary_line()
        assert result  # no crash


# ── persistence across instances ────────────────────────────────────

class TestPersistence:
    def test_streak_persists_across_instances(self, tmp_path):
        habits_dir = tmp_path / "habits"
        habits_dir.mkdir()
        (habits_dir / "current_habits.json").write_text(
            json.dumps({"habits": [{"name": "Run", "streak": 3, "target": 30}]})
        )
        ci1 = HabitCheckIn(tmp_path)
        ci1.check_in([0])

        ci2 = HabitCheckIn(tmp_path)  # new instance
        status = ci2.today_status()
        assert status[0]["streak"] == 4
        assert status[0]["done"] is True

    def test_add_habit_persists_across_instances(self, tmp_path):
        (tmp_path / "habits").mkdir()
        (tmp_path / "habits" / "current_habits.json").write_text(json.dumps({"habits": []}))
        ci1 = HabitCheckIn(tmp_path)
        ci1.add_habit("Sleep early")

        ci2 = HabitCheckIn(tmp_path)
        names = [h["name"] for h in ci2.today_status()]
        assert "Sleep early" in names
