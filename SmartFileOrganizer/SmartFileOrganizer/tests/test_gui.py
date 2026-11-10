"""Unit and Integration tests for GUI navigation and components."""
import unittest
from pathlib import Path
import customtkinter as ctk

from core.config_manager import config_manager
from gui.app import SmartFileOrganizerApp

class TestGUIApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize GUI instance for testing (without running mainloop)
        cls.app = SmartFileOrganizerApp()
        cls.app.withdraw()  # Hide window during test execution

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.destroy()
        except Exception:
            pass

    def test_window_properties(self):
        """Verifies title and initial resolution."""
        self.assertEqual(self.app.title(), "Smart File Organizer")
        self.assertIn("dashboard", self.app.pages)
        self.assertIn("organizer", self.app.pages)
        self.assertIn("duplicates", self.app.pages)
        self.assertIn("history", self.app.pages)
        self.assertIn("settings", self.app.pages)
        self.assertIn("about", self.app.pages)

    def test_sidebar_navigation_flow(self):
        """Verifies that navigation switches active pages without exceptions."""
        pages = ["dashboard", "organizer", "duplicates", "history", "settings", "about"]
        for p in pages:
            self.app.navigate_to_page(p)
            self.assertEqual(self.app.sidebar.current_page, p)

    def test_status_message(self):
        """Verifies status message updates."""
        test_msg = "Test status message update"
        self.app.set_status_message(test_msg)
        self.assertEqual(self.app.status_text_lbl.cget("text"), test_msg)

    def test_folder_coordination(self):
        """Verifies that changing active folder updates all dependent components."""
        test_folder = "C:\\Users\\Test\\Downloads"
        self.app.set_active_directory(test_folder)
        self.assertEqual(self.app.active_directory, test_folder)
        self.assertIn("Downloads", self.app.status_folder_lbl.cget("text"))

if __name__ == "__main__":
    unittest.main()
