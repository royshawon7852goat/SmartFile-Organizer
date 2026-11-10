# Smart File Organizer

A modern, high-performance Windows desktop application built with Python and CustomTkinter for automated file organization, SHA-256 duplicate quarantine, and non-destructive undo operations.

Designed with a Windows 11 dark theme, fluent typography, and safety safeguards.

---

## Key Features

- **Automated Category Organization**: Sorts messy folders into structured subfolders (`Documents/`, `Images/`, `Videos/`, `Audio/`, `Archives/`, `Applications/`, and `Others/`).
- **Interactive Dry-Run Preview**: Inspect planned movements, sizes, and destinations in a preview table before touching any files on disk.
- **SHA-256 Duplicate Finder**: Memory-efficient streaming duplicate detection using initial file-size pre-filtering and 64KB chunked SHA-256 hashing.
- **Guaranteed Safe Quarantine**: **Never** deletes duplicate files automatically. Extra copies are safely isolated into dedicated `Duplicate_Review_<timestamp>` folders with one-click Explorer access.
- **Reversible Undo System**: Revert any organization session with a single click. Files are restored to their original paths and empty category folders are removed.
- **Collision-Proof Renaming**: If a destination file already exists, it is never overwritten; names are automatically incremented (`file (1).ext`).
- **Windows System Directory Guard**: Actively blocks modification to critical Windows locations (`C:\`, `C:\Windows`, `System32`, `Program Files`, `ProgramData`, and the app's own directory).
- **Persistent Activity History**: Stores detailed audit records of files moved, timestamp, directory, and status in `data/history.json`.
- **Customizable Categories & Theme**: Add, edit, or remove file extensions per category and switch between Dark, Light, and System themes.

---

## Project Structure

```
SmartFileOrganizer/
│
├── main.py                     # Application entry point with High-DPI awareness
├── build_exe.py                # Standalone Windows executable builder
├── requirements.txt            # Lightweight dependencies
├── config.json                 # Persistent configuration settings
├── README.md                   # Documentation & installation guide
│
├── assets/
│   ├── generate_assets.py      # Pillow asset generator
│   ├── icons/                  # app_icon.ico, app_icon.png
│   └── images/                 # App artwork
│
├── core/
│   ├── __init__.py             # Core package initialization
│   ├── config_manager.py       # Configuration manager
│   ├── security.py             # System directory guard & safe naming
│   ├── file_scanner.py         # Directory scanner
│   ├── organizer.py            # File categorization engine
│   ├── duplicate_finder.py     # Chunked SHA-256 duplicate detector
│   ├── history_manager.py      # Audit log & statistics calculator
│   ├── undo_manager.py         # Non-destructive file restorer
│   └── logger.py               # Rotating application logger
│
├── gui/
│   ├── __init__.py             # GUI package initialization
│   ├── app.py                  # Main Window (ctk.CTk)
│   ├── sidebar.py              # Windows 11 style navigation sidebar
│   ├── dashboard.py            # Statistics cards & category charts
│   ├── organizer_page.py       # Folder categorization & live preview
│   ├── duplicate_page.py       # Duplicate detection & quarantine
│   ├── history_page.py         # Session history & inspection
│   ├── settings_page.py        # Preferences & extension editor
│   ├── about_page.py           # Specifications & architecture
│   └── components/
│       ├── stat_card.py        # Rounded hoverable metric card
│       ├── toast.py            # Confirmation modals & alerts
│       ├── preview_modal.py    # Dry-run inspection modal
│       └── history_modal.py    # Per-session file detail inspector
│
├── data/
│   └── history.json            # Persistent session history store
│
├── logs/
│   └── app.log                 # Rotating debug and execution logs
│
└── tests/
    ├── test_core.py            # Unit tests for core operations
    ├── test_gui.py             # Integration tests for GUI navigation
    └── test_extended.py        # Edge cases & collision avoidance tests
```

---

## Installation & Setup

### Prerequisites

- Windows 10 or Windows 11 (64-bit recommended)
- Python 3.12+ (Tested on Python 3.14)

### 1. Clone or Extract the Project

Open PowerShell in the project directory:

```powershell
cd c:\Users\roysh\Downloads\SmartFileOrganizer
```

### 2. (Optional) Create a Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## Running the Application

Launch the desktop GUI using PowerShell:

```powershell
python main.py
```

---

## Running Automated Tests

Run the complete test suite (unit tests, integration tests, collision handling, and edge cases):

```powershell
python -m unittest discover tests
```

---

## Building Standalone Windows Executable (.exe)

You can package the application into a standalone Windows executable (`SmartFileOrganizer.exe`) that launches without opening a command prompt or terminal.

### 1. Install PyInstaller

```powershell
pip install pyinstaller
```

### 2. Build the Executable

Run the automated build script:

```powershell
python build_exe.py
```

Or execute PyInstaller directly via PowerShell:

```powershell
pyinstaller --noconsole --name "SmartFileOrganizer" --icon "assets/icons/app_icon.ico" --add-data "assets;assets" --collect-all customtkinter --clean --noconfirm main.py
```

### 3. Launch the Executable

The compiled application will be generated in `dist\SmartFileOrganizer\SmartFileOrganizer.exe`:

```powershell
.\dist\SmartFileOrganizer\SmartFileOrganizer.exe
```

Double-click `SmartFileOrganizer.exe` in Windows File Explorer to launch the application.

---

## Default Category Mapping

| Category | File Extensions |
| :--- | :--- |
| **Documents** | `.pdf`, `.doc`, `.docx`, `.txt`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.csv` |
| **Images** | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`, `.webp` |
| **Videos** | `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv` |
| **Audio** | `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg` |
| **Archives** | `.zip`, `.rar`, `.7z`, `.tar`, `.gz` |
| **Applications** | `.exe`, `.msi` |
| **Others** | All unrecognized formats |

*Extensions can be customized in the **Settings** tab.*

---

## Safety Guarantees

1. **Never Overwrites**: Duplicate file names at destination are incremented to `name (1).ext`.
2. **Never Automatically Deletes**: Duplicates are moved to a `Duplicate_Review_<timestamp>` folder.
3. **Protected Directories**: Blocks system folders (`C:\Windows`, `Program Files`, root drives `C:\`, etc.).
4. **Reliable Undo**: Restores organized files to their original paths and cleans up empty category folders.
5. **Safe History Wipe**: Clearing activity history purges records from the database without touching user files on disk.
