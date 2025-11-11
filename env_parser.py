"""
Environment File Parser
Discovers .env files in project directories
"""
from pathlib import Path


def find_env_files(directory: Path | str) -> list[Path]:
    """
    Find all .env files recursively in a directory
    Matches patterns: *.env and *.env.*

    Args:
        directory: Directory to search for .env files

    Returns:
        List of paths to .env files found
    """
    if isinstance(directory, str):
        directory = Path(directory)

    if not directory.exists() or not directory.is_dir():
        return []

    env_files = []

    # Recursively find all files matching *.env or *.env.*
    for path in directory.rglob("*"):
        if path.is_file():
            # Match blah.env or blah.env.blah
            if path.suffix == ".env" or ".env." in path.name:
                env_files.append(path)

    # Sort by name for consistent ordering
    env_files.sort(key=lambda p: p.name.lower())

    return env_files
