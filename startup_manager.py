"""
Startup Manager - Add/remove launcher from Windows startup
"""
from pathlib import Path
import os
import sys
import win32com.client


class StartupManager:
    """Manage adding/removing the launcher from Windows startup"""

    def __init__(self, launcher_script: Path):
        self.launcher_script = launcher_script
        self.startup_dir = Path(os.getenv('APPDATA')) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        self.batch_name = "python_launcher_startup.bat"
        self.shortcut_name = "Python App Launcher.lnk"
        self.batch_path = launcher_script.parent / self.batch_name
        self.shortcut_path = self.startup_dir / self.shortcut_name

    def is_in_startup(self) -> bool:
        """Check if launcher is currently in startup"""
        return self.shortcut_path.exists()

    def add_to_startup(self) -> bool:
        """Add launcher to startup"""
        try:
            # Detect venv
            venv_path = self._detect_venv()

            # Create batch file
            batch_lines = ["@echo off", ""]

            # Change to launcher directory
            batch_lines.append(f'cd /d "{self.launcher_script.parent}"')

            # Activate venv if exists
            if venv_path:
                activate_script = venv_path / "Scripts" / "activate.bat"
                batch_lines.append(f'call "{activate_script}"')

            # Run the launcher (without showing console window)
            batch_lines.append(f'start /B pythonw "{self.launcher_script.name}"')

            # Write batch file
            with open(self.batch_path, 'w') as f:
                f.write('\n'.join(batch_lines))

            # Create shortcut to batch file
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(self.shortcut_path))
            shortcut.TargetPath = str(self.batch_path)
            shortcut.WorkingDirectory = str(self.launcher_script.parent)
            shortcut.IconLocation = sys.executable  # Python icon
            shortcut.WindowStyle = 7  # Minimized
            shortcut.save()

            return True

        except Exception as e:
            print(f"Error adding to startup: {e}")
            return False

    def remove_from_startup(self) -> bool:
        """Remove launcher from startup"""
        try:
            # Remove shortcut
            if self.shortcut_path.exists():
                self.shortcut_path.unlink()

            # Remove batch file
            if self.batch_path.exists():
                self.batch_path.unlink()

            return True

        except Exception as e:
            print(f"Error removing from startup: {e}")
            return False

    def _detect_venv(self) -> Path | None:
        """Detect virtual environment"""
        # Check common venv locations relative to launcher script
        script_dir = self.launcher_script.parent
        parent_dir = script_dir.parent

        venv_names = ['venv', '.venv', 'env', '.env', 'virtualenv']

        # Check parent directory (most likely location)
        for venv_name in venv_names:
            venv_path = parent_dir / venv_name
            if (venv_path / "Scripts" / "python.exe").exists():
                return venv_path

        # Check script directory
        for venv_name in venv_names:
            venv_path = script_dir / venv_name
            if (venv_path / "Scripts" / "python.exe").exists():
                return venv_path

        return None
