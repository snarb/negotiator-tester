import sqlite3
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import main


class SmokeTest(unittest.TestCase):
    def test_app_imports_and_serves_root(self):
        client = TestClient(main.app)

        response = client.get("/")

        self.assertIn(response.status_code, {200, 404})

    def test_config_is_complete(self):
        self.assertEqual(main.CONFIG_ERRORS, [])

    def test_db_polling_reports_missing_db_path(self):
        original_db_path = main.NEGOTIATOR_DB_PATH
        original_reported_facts = main.reported_db_facts.copy()
        original_debug_history = main.debug_history.copy()
        original_db_status = main.db_debug_status.copy()

        try:
            main.NEGOTIATOR_DB_PATH = ""
            main.reported_db_facts.clear()
            main.debug_history.clear()
            main.db_debug_status.clear()

            main.check_db_for_updates("ticket-123")

            self.assertIn("db_path_missing", main.render_debug_panel("ticket-123"))
        finally:
            main.NEGOTIATOR_DB_PATH = original_db_path
            main.reported_db_facts.clear()
            main.reported_db_facts.update(original_reported_facts)
            main.debug_history.clear()
            main.debug_history.update(original_debug_history)
            main.db_debug_status.clear()
            main.db_debug_status.update(original_db_status)

    def test_db_polling_reports_read_errors(self):
        original_db_path = main.NEGOTIATOR_DB_PATH
        original_reported_facts = main.reported_db_facts.copy()
        original_debug_history = main.debug_history.copy()
        original_db_status = main.db_debug_status.copy()

        try:
            main.NEGOTIATOR_DB_PATH = "C:\\repos\\negotiator\\negotiator.db"
            main.reported_db_facts.clear()
            main.debug_history.clear()
            main.db_debug_status.clear()

            with patch("main.os.path.exists", return_value=True), patch(
                "main.sqlite3.connect", side_effect=sqlite3.OperationalError("boom")
            ):
                main.check_db_for_updates("ticket-123")

            panel = main.render_debug_panel("ticket-123")
            self.assertIn("db_read_error", panel)
            self.assertIn("boom", panel)
        finally:
            main.NEGOTIATOR_DB_PATH = original_db_path
            main.reported_db_facts.clear()
            main.reported_db_facts.update(original_reported_facts)
            main.debug_history.clear()
            main.debug_history.update(original_debug_history)
            main.db_debug_status.clear()
            main.db_debug_status.update(original_db_status)

    def test_selected_arms_are_read_from_ticket_metadata_object(self):
        row = {
            "metadata": {
                "selected_arms": {
                    "persona": "persona_arm_1",
                    "J1": "j1_arm_2",
                    "J2": "j2_arm_3",
                    "J4": "j4_arm_4",
                    "J5": "j5_arm_5",
                }
            }
        }

        class RowLike(dict):
            def __getitem__(self, item):
                return dict.__getitem__(self, item)

        extracted = main.extract_selected_arms(RowLike(row))

        self.assertEqual(
            extracted,
            [
                "persona: persona_arm_1",
                "J1: j1_arm_2",
                "J2: j2_arm_3",
                "J4: j4_arm_4",
                "J5: j5_arm_5",
            ],
        )


if __name__ == "__main__":
    unittest.main()
