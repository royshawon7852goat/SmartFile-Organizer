"""Core package for Smart File Organizer."""
from core.config_manager import config_manager
from core.security import is_safe_directory, is_hidden_or_system, get_safe_destination
from core.file_scanner import file_scanner, ScannedFile
from core.organizer import file_organizer, OrganizationAction, OrganizationResult
from core.duplicate_finder import duplicate_finder, DuplicateGroup
from core.history_manager import history_manager
from core.undo_manager import undo_manager
from core.logger import logger

__all__ = [
    "config_manager",
    "is_safe_directory",
    "is_hidden_or_system",
    "get_safe_destination",
    "file_scanner",
    "ScannedFile",
    "file_organizer",
    "OrganizationAction",
    "OrganizationResult",
    "duplicate_finder",
    "DuplicateGroup",
    "history_manager",
    "undo_manager",
    "logger",
]
