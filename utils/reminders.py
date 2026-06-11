"""Reminders module — load and check daily reminders"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class ReminderManager:
    def __init__(self, reminders_dir: Path):
        self.dir = reminders_dir
        self.dir.mkdir(exist_ok=True)
        self.file = self.dir / "reminders.json"
        if not self.file.exists():
            self._create_defaults()

    def _create_defaults(self):
        defaults = [
            {"time": "07:30", "message": "Drink a glass of water 💧",        "date": "daily"},
            {"time": "09:00", "message": "Check your task list 📋",            "date": "daily"},
            {"time": "13:00", "message": "Take a lunch break 🍽️",             "date": "daily"},
            {"time": "17:00", "message": "Evening walk or stretch 🚶",         "date": "daily"},
            {"time": "22:00", "message": "Wind down — no screens in 30 min 😴", "date": "daily"},
        ]
        self.file.write_text(json.dumps(defaults, indent=2))

    def get_due_today(self) -> List[Dict[str, Any]]:
        reminders = json.loads(self.file.read_text())
        today = datetime.now().strftime("%Y-%m-%d")
        return [
            r for r in reminders
            if r.get("date") == "daily" or r.get("date") == today
        ]

    def add(self, time: str, message: str, date: str = "daily"):
        reminders = json.loads(self.file.read_text())
        reminders.append({"time": time, "message": message, "date": date})
        self.file.write_text(json.dumps(reminders, indent=2))
        print(f"  ✅ Reminder added: [{time}] {message}")
