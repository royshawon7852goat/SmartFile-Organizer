"""Comprehensive Unit and Integration Tests for Core Modules."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from core.config_manager import ConfigManager
from core.duplicate_finder import DuplicateFinder
from core.file_scanner import FileScanner
from core.history_manager import HistoryManager
from core.organizer import FileOrganizer
from core.security import get_safe_destination, is_safe_directory
from core.undo_manager import UndoManager

class TestCoreModules(unittest.TestCase):

    def setUp(self):
        # Create a dedicated temp workspace
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sfo_test_"))
        self.config_path = self.temp_dir / "test_config.json"
        self.history_path = self.temp_dir / "test_history.json"

        self.config_mgr = ConfigManager(self.config_path)
        self.history_mgr = HistoryManager(self.history_path)
        self.scanner = FileScanner()
        self.organizer = FileOrganizer(self.history_mgr)
        self.duplicate_finder = DuplicateFinder(self.history_mgr)
        self.undo_mgr = UndoManager(self.history_mgr)

    def tearDown(self):
        # Clean up temp folder
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_security_validation(self):
        """Tests directory safety rules."""
        # Safe directory
        safe_folder = self.temp_dir / "SafeFolder"
        safe_folder.mkdir()
        is_safe, reason = is_safe_directory(safe_folder)
        self.assertTrue(is_safe, f"Safe directory should pass: {reason}")

        # Root drive (e.g. C:\)
        is_safe, reason = is_safe_directory(Path("C:\\"))
        self.assertFalse(is_safe)
        self.assertIn("root drive", reason.lower())

    def test_safe_destination_collision_avoidance(self):
        """Tests that get_safe_destination creates non-overwriting filenames."""
        folder = self.temp_dir / "collision_test"
        folder.mkdir()

        f1 = folder / "report.pdf"
        f1.write_text("v1")

        dest1 = get_safe_destination(folder, "report.pdf")
        self.assertEqual(dest1.name, "report (1).pdf")

        dest1.write_text("v2")
        dest2 = get_safe_destination(folder, "report.pdf")
        self.assertEqual(dest2.name, "report (2).pdf")

    def test_organization_and_undo_lifecycle(self):
        """Tests scanning, preview, execution, and full undo."""
        folder = self.temp_dir / "organize_test"
        folder.mkdir()

        # Create dummy test files
        test_files = {
            "document.pdf": "doc content",
            "photo.jpg": "image content",
            "audio.mp3": "sound content",
            "video.mp4": "movie content",
            "archive.zip": "compressed content",
            "app.exe": "binary content",
            "data.unknown": "custom format",
        }
        for name, content in test_files.items():
            (folder / name).write_text(content)

        # Preview
        valid, err, actions = self.organizer.preview_organization(folder)
        self.assertTrue(valid, err)
        self.assertEqual(len(actions), 7)

        # Verify category mapping in actions
        cat_map = {a.filename: a.category for a in actions}
        self.assertEqual(cat_map["document.pdf"], "Documents")
        self.assertEqual(cat_map["photo.jpg"], "Images")
        self.assertEqual(cat_map["audio.mp3"], "Audio")
        self.assertEqual(cat_map["video.mp4"], "Videos")
        self.assertEqual(cat_map["archive.zip"], "Archives")
        self.assertEqual(cat_map["app.exe"], "Applications")
        self.assertEqual(cat_map["data.unknown"], "Others")

        # Execute
        result = self.organizer.execute_organization(folder, actions)
        self.assertEqual(result.moved_count, 7)
        self.assertEqual(result.failed_count, 0)
        self.assertIsNotNone(result.session_id)

        # Verify files are now inside their respective folders
        self.assertTrue((folder / "Documents" / "document.pdf").exists())
        self.assertTrue((folder / "Images" / "photo.jpg").exists())
        self.assertTrue((folder / "Audio" / "audio.mp3").exists())
        self.assertTrue((folder / "Videos" / "video.mp4").exists())
        self.assertTrue((folder / "Archives" / "archive.zip").exists())
        self.assertTrue((folder / "Applications" / "app.exe").exists())
        self.assertTrue((folder / "Others" / "data.unknown").exists())

        # Verify original files in root no longer exist
        for name in test_files:
            self.assertFalse((folder / name).exists())

        # Now test UNDO
        ok, msg, undo_res = self.undo_mgr.undo_session(result.session_id)
        self.assertTrue(ok, msg)
        self.assertEqual(undo_res.restored_count, 7)
        self.assertEqual(undo_res.failed_count, 0)

        # Verify files are restored back to root folder
        for name, content in test_files.items():
            restored = folder / name
            self.assertTrue(restored.exists(), f"File {name} should be restored.")
            self.assertEqual(restored.read_text(), content)

        # Verify empty category folders were cleaned up
        for cat in ["Documents", "Images", "Audio", "Videos", "Archives", "Applications", "Others"]:
            self.assertFalse((folder / cat).exists(), f"Folder {cat} should be removed after undo.")

    def test_duplicate_detection_and_safe_move(self):
        """Tests SHA-256 chunked duplicate identification and moving to review folder."""
        folder = self.temp_dir / "dup_test"
        folder.mkdir()

        # Create two identical files and one unique file
        shared_content = "Identical SHA-256 binary/text data " * 100
        (folder / "original.txt").write_text(shared_content)
        (folder / "copy1.txt").write_text(shared_content)
        (folder / "copy2.txt").write_text(shared_content)
        (folder / "different.txt").write_text("Different content entirely")

        # Scan duplicates
        valid, err, groups = self.duplicate_finder.scan_duplicates(folder, recursive=False)
        self.assertTrue(valid, err)
        self.assertEqual(len(groups), 1)

        group = groups[0]
        self.assertEqual(len(group.files), 3)
        self.assertEqual(group.file_size, len(shared_content.encode("utf-8")))

        # Test moving 2 duplicates to review folder (keeping the first one in group)
        kept_file = group.files[0].path
        files_to_move = [f.path for f in group.files[1:]]  # move 2 copies
        moved, failed, errors, review_dir = self.duplicate_finder.move_selected_duplicates(
            folder, files_to_move
        )
        self.assertEqual(moved, 2)
        self.assertEqual(failed, 0)
        self.assertTrue(review_dir.exists())

        # Kept copy is still in folder
        self.assertTrue(kept_file.exists())
        # The 2 copies are moved into review folder
        review_files = list(review_dir.glob("*.txt"))
        self.assertEqual(len(review_files), 2)

    def test_history_statistics(self):
        """Tests statistics aggregation in HistoryManager."""
        self.history_mgr.add_session(
            directory="C:/test",
            files_scanned=10,
            files_moved=10,
            files_failed=0,
            records=[
                {"category": "Documents", "size_bytes": 1000, "status": "moved"},
                {"category": "Images", "size_bytes": 2000, "status": "moved"},
            ],
            session_type="organize"
        )
        stats = self.history_mgr.get_aggregate_statistics()
        self.assertEqual(stats["total_files_scanned"], 10)
        self.assertEqual(stats["total_files_organized"], 10)
        self.assertEqual(stats["total_bytes_organized"], 3000)
        self.assertEqual(stats["category_distribution"]["Documents"], 1)
        self.assertEqual(stats["category_distribution"]["Images"], 1)

if __name__ == "__main__":
    unittest.main()
