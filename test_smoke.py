import unittest

from fastapi.testclient import TestClient

import main


class SmokeTest(unittest.TestCase):
    def test_app_imports_and_serves_root(self):
        client = TestClient(main.app)

        response = client.get("/")

        self.assertIn(response.status_code, {200, 404})

    def test_missing_env_vars_are_reported(self):
        self.assertEqual(
            set(main.CONFIG_ERRORS),
            {
                "NEGOTIATOR_API_URL",
                "NEGOTIATOR_INBOUND_BEARER_TOKEN",
                "NEGOTIATOR_OUTBOUND_BEARER_TOKEN",
                "NEGOTIATOR_DB_PATH",
            },
        )

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


if __name__ == "__main__":
    unittest.main()
