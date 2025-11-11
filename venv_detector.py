"""
Virtual Environment Detector
Automatically discovers virtual environments for Python projects
"""
from pathlib import Path


def detect_venv(script_path: Path | str) -> Path | None:
    """
    Detect virtual environment for a given script path

    Args:
        script_path: Path to the Python script

    Returns:
        Path to detected venv or None if not found
    """
    if isinstance(script_path, str):
        script_path = Path(script_path)

    script_dir = script_path.parent if script_path.is_file() else script_path
    parent_dir = script_dir.parent

    # Common venv directory names
    venv_names = ['venv', '.venv', 'virtualenv']

    # Check parent directory first (most common location)
    for venv_name in venv_names:
        venv_path = parent_dir / venv_name
        if (venv_path / "Scripts" / "python.exe").exists():
            return venv_path

    # Check script directory
    for venv_name in venv_names:
        venv_path = script_dir / venv_name
        if (venv_path / "Scripts" / "python.exe").exists():
            return venv_path

    # Check grandparent directory
    grandparent_dir = parent_dir.parent
    for venv_name in venv_names:
        venv_path = grandparent_dir / venv_name
        if (venv_path / "Scripts" / "python.exe").exists():
            return venv_path

    return None
