"""Extended edge case and integration tests for Smart File Organizer."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from core.config_manager import ConfigManager
from core.duplicate_finder import DuplicateFinder
from core.history_manager import HistoryManager
from core.organizer import FileOrganizer
from core.security import is_safe_directory, get_safe_destination
from core.undo_manager import UndoManager

class TestExtendedEdgeCases(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sfo_edge_"))
        self.config_path = self.temp_dir / "test_config.json"
        self.history_path = self.temp_dir / "test_history.json"

        self.config_mgr = ConfigManager(self.config_path)
        self.history_mgr = HistoryManager(self.history_path)
        self.organizer = FileOrganizer(self.history_mgr)
        self.duplicate_finder = DuplicateFinder(self.history_mgr)
        self.undo_mgr = UndoManager(self.history_mgr)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_destination_collision_handling_on_organize(self):
        """Tests that moving a file with existing destination does NOT overwrite, but increments safely."""
        folder = self.temp_dir / "collision_folder"
        folder.mkdir()

        # Pre-create category folder with existing file
        docs_dir = folder / "Documents"
        docs_dir.mkdir()
        existing_doc = docs_dir / "notes.txt"
        existing_doc.write_text("Original existing document content")

        # Source file in root with the exact same name
        source_doc = folder / "notes.txt"
        source_doc.write_text("New incoming document content")

        # Execute organization
        result = self.organizer.execute_organization(folder)
        self.assertEqual(result.moved_count, 1)

        # Original doc must be unchanged
        self.assertEqual(existing_doc.read_text(), "Original existing document content")

        # New file must have been renamed safely to 'notes (1).txt'
        safely_renamed = docs_dir / "notes (1).txt"
        self.assertTrue(safely_renamed.exists())
        self.assertEqual(safely_renamed.read_text(), "New incoming document content")

    def test_custom_category_extension_mapping(self):
        """Tests adding custom extensions in config manager."""
        custom_categories = {
            "Documents": [".pdf", ".txt", ".md", ".rtf"],
            "Code": [".py", ".js", ".html", ".css"],
            "Images": [".png", ".jpg"],
            "Others": []
        }
        self.config_mgr.update_categories(custom_categories)

        self.assertEqual(self.config_mgr.get_category_for_ext(".py"), "Code")
        self.assertEqual(self.config_mgr.get_category_for_ext(".md"), "Documents")
        self.assertEqual(self.config_mgr.get_category_for_ext(".unknownxyz"), "Others")

    def test_clear_history_does_not_affect_files(self):
        """Tests that clearing history leaves actual files untouched."""
        folder = self.temp_dir / "clear_hist_test"
        folder.mkdir()

        test_file = folder / "data.csv"
        test_file.write_text("1,2,3")

        # Organize
        res = self.organizer.execute_organization(folder)
        self.assertEqual(res.moved_count, 1)
        target_file = folder / "Documents" / "data.csv"
        self.assertTrue(target_file.exists())

        # Clear history
        self.history_mgr.clear_history()
        self.assertEqual(len(self.history_mgr.get_all_sessions()), 0)

        # File must still be intact on disk!
        self.assertTrue(target_file.exists())
        self.assertEqual(target_file.read_text(), "1,2,3")

    def test_prevent_organizing_app_installation_directory(self):
        """Verifies that the app's own directory is recognized as unsafe."""
        from core.security import BASE_DIR
        is_safe, reason = is_safe_directory(BASE_DIR)
        self.assertFalse(is_safe)
        self.assertIn("installation", reason.lower())

if __name__ == "__main__":
    unittest.main()
