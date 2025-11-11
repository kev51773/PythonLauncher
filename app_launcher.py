"""
Application launcher - launches Python apps with detached processes
"""
import subprocess
import os
from pathlib import Path
from typing import Optional, List
import sys


def parse_env_file(env_file_path: Path) -> dict:
    """
    Parse a .env file and return environment variables.

    Args:
        env_file_path: Path to the .env file

    Returns:
        Dictionary of environment variable name -> value
    """
    import re
    env_vars = {}

    try:
        with open(env_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE format
                match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$', line)
                if match:
                    key = match.group(1)
                    value = match.group(2)

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    env_vars[key] = value

    except Exception as e:
        print(f"Warning: Failed to parse {env_file_path}: {e}")

    return env_vars


def launch_app(
    script_path: Path,
    parameters: str = "",
    venv_path: Optional[Path] = None,
    env_files: Optional[List[Path]] = None,
    working_directory: Optional[Path] = None
) -> bool:
    """
    Launch a Python application in a detached process.

    Args:
        script_path: Path to the Python script
        parameters: Command line parameters
        venv_path: Optional virtual environment path
        env_files: Optional list of .env files to load
        working_directory: Optional working directory (defaults to script directory)

    Returns:
        True if launch succeeded, False otherwise
    """
    try:
        # Determine working directory
        if working_directory:
            cwd = str(working_directory)
        else:
            cwd = str(script_path.parent)

        # Create a temporary batch file
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        batch_file = temp_dir / f"launcher_{script_path.stem}_{os.getpid()}.bat"

        # Build the batch file content
        batch_lines = ["@echo off", ""]

        # Change to working directory
        batch_lines.append(f'cd /d "{cwd}"')
        batch_lines.append("")

        # Load .env files if provided
        if env_files:
            for env_file in env_files:
                if env_file.exists():
                    env_vars = parse_env_file(env_file)
                    if env_vars:
                        batch_lines.append(f"REM Load environment variables from {env_file.name}")
                        for key, value in env_vars.items():
                            # Escape special characters in batch files
                            escaped_value = value.replace("%", "%%")
                            batch_lines.append(f'set {key}={escaped_value}')
                        batch_lines.append("")

        # Activate venv if specified
        if venv_path:
            activate_script = venv_path / "Scripts" / "activate.bat"
            if not activate_script.exists():
                print(f"Error: Venv activation script not found: {activate_script}")
                return False

            batch_lines.append("REM Activate virtual environment")
            batch_lines.append(f'call "{activate_script}"')
            batch_lines.append("")

        # Build Python command
        batch_lines.append("REM Run Python script")

        # Add parameters (split by spaces, respecting quotes)
        if parameters:
            import shlex
            params = ' '.join(shlex.split(parameters))
            batch_lines.append(f'python "{script_path.resolve()}" {params}')
        else:
            batch_lines.append(f'python "{script_path.resolve()}"')

        # Add pause at end
        batch_lines.append("")
        batch_lines.append("echo.")
        batch_lines.append("echo Process finished. Press any key to close...")
        batch_lines.append("pause > nul")

        # Write batch file
        with open(batch_file, 'w') as f:
            f.write('\n'.join(batch_lines))

        # Use 'start' command to open a new visible console window
        full_cmd = f'start "Python App" cmd /K "{batch_file}"'

        # Debug output
        print(f"Launching script: {script_path.resolve()}")
        print(f"Working directory: {cwd}")
        if venv_path:
            print(f"Virtual environment: {venv_path}")
        if parameters:
            print(f"Parameters: {parameters}")
        print(f"Batch file: {batch_file}")

        # Launch process using cmd.exe with 'start' command
        # shell=True is required for 'start' to work
        process = subprocess.Popen(
            full_cmd,
            shell=True
        )

        print(f"Process started with PID: {process.pid}")

        return True

    except Exception as e:
        print(f"Error launching app: {e}")
        import traceback
        traceback.print_exc()
        return False
