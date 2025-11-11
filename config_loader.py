"""
Configuration loader for app launcher
"""
import json
from pathlib import Path
from typing import List, Dict, Optional


class AppConfig:
    """Represents a single app configuration"""

    def __init__(self, config_path: Path, data: dict):
        self.config_path = config_path
        self.config_name = config_path.stem

        # Required fields
        self.name = data.get("name", self.config_name)
        self.script = Path(data["script"]) if "script" in data else None

        # Optional fields
        self.icon = Path(data["icon"]) if "icon" in data else None
        self.venv = Path(data["venv"]) if "venv" in data else None
        self.working_directory = Path(data.get("working_directory", "")) if "working_directory" in data else None
        self.description = data.get("description", "")

        # Env files
        self.env_files = [Path(f) for f in data.get("env_files", [])]
        self.env_directory = Path(data["env_directory"]) if "env_directory" in data else None

        # Variables and parameter sets
        self.variables = data.get("variables", {})
        self.parameter_sets = data.get("parameter_sets", [])

    def get_all_env_files(self) -> List[Path]:
        """
        Get all env files from both explicit list and directory scan.
        Returns merged list with duplicates removed.
        """
        env_files = set()

        # Add explicitly listed env files
        for env_file in self.env_files:
            if env_file.exists():
                env_files.add(env_file.resolve())

        # Scan env directory if specified
        if self.env_directory and self.env_directory.exists():
            for file_path in self.env_directory.rglob("*"):
                if not file_path.is_file():
                    continue

                filename = file_path.name
                # Match .env patterns
                if (filename == ".env" or
                    filename.endswith(".env") or
                    ".env." in filename):
                    env_files.add(file_path.resolve())

        return sorted(list(env_files))

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the configuration.
        Returns (is_valid, error_message)
        """
        if not self.script:
            return False, "Missing required field: script"

        if not self.script.exists():
            return False, f"Script not found: {self.script}"

        if self.venv and not (self.venv / "Scripts" / "python.exe").exists():
            return False, f"Invalid venv: {self.venv}"

        return True, None


class ConfigLoader:
    """Loads and manages app configurations"""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.master_config_path = config_dir / "master.json"

    def load_all_configs(self) -> List[AppConfig]:
        """
        Load all app configurations from the config directory.
        Returns list sorted by master.json order if it exists, otherwise alphabetically.
        """
        configs = {}

        # Load all JSON files except master.json
        for config_file in self.config_dir.glob("*.json"):
            if config_file.name == "master.json":
                continue

            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config = AppConfig(config_file, data)

                    # Validate config
                    is_valid, error = config.validate()
                    if is_valid:
                        configs[config.config_name] = config
                    else:
                        print(f"Warning: Invalid config {config_file.name}: {error}")

            except Exception as e:
                print(f"Warning: Failed to load {config_file.name}: {e}")

        # Sort configs
        return self._sort_configs(configs)

    def _sort_configs(self, configs: Dict[str, AppConfig]) -> List[AppConfig]:
        """Sort configs by master.json order, then alphabetically"""

        # Try to load master config
        custom_order = []
        if self.master_config_path.exists():
            try:
                with open(self.master_config_path, 'r', encoding='utf-8') as f:
                    master_data = json.load(f)
                    custom_order = master_data.get("order", [])
            except Exception as e:
                print(f"Warning: Failed to load master.json: {e}")

        # Sort by custom order first, then alphabetically
        sorted_configs = []

        # Add configs in custom order
        for config_name in custom_order:
            if config_name in configs:
                sorted_configs.append(configs[config_name])
                del configs[config_name]

        # Add remaining configs alphabetically
        remaining = sorted(configs.values(), key=lambda c: c.name.lower())
        sorted_configs.extend(remaining)

        return sorted_configs
