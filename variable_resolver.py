"""
Variable resolver for parameter substitution
"""
import re
import tkinter as tk
from tkinter import filedialog, simpledialog
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import pyperclip


class VariableResolver:
    """Resolves variables in parameter strings"""

    def __init__(self, variables_config: Dict):
        """
        Initialize with variables configuration from app config.

        Args:
            variables_config: Dictionary of variable definitions from JSON
        """
        self.variables_config = variables_config
        self.resolved_values = {}

    def resolve_parameters(self, params: str) -> Optional[str]:
        """
        Resolve all variables in a parameter string.

        Args:
            params: Parameter string with $variables

        Returns:
            Resolved parameter string, or None if user cancelled
        """
        # Find all $variable references
        pattern = r'\$(\w+)'
        variables_found = re.findall(pattern, params)

        # Resolve each unique variable
        for var_name in set(variables_found):
            if var_name not in self.resolved_values:
                value = self._resolve_variable(var_name)
                if value is None:
                    # User cancelled
                    return None
                self.resolved_values[var_name] = value

        # Substitute all variables in params
        def replace_var(match):
            var_name = match.group(1)
            return self.resolved_values.get(var_name, match.group(0))

        return re.sub(pattern, replace_var, params)

    def _resolve_variable(self, var_name: str) -> Optional[str]:
        """
        Resolve a single variable by prompting user or using built-in values.

        Returns:
            Variable value, or None if user cancelled
        """
        if var_name not in self.variables_config:
            print(f"Warning: Unknown variable ${var_name}")
            return f"${var_name}"

        var_config = self.variables_config[var_name]
        var_type = var_config.get("type", "input")
        default = var_config.get("default", "")

        if var_type == "filepicker":
            return self._prompt_file_picker(var_config, default)

        elif var_type == "folderpicker":
            return self._prompt_folder_picker(var_config, default)

        elif var_type == "input":
            return self._prompt_input(var_config, default)

        elif var_type == "datetime":
            # Support custom format via 'format' field, with sensible defaults
            format_str = var_config.get("format", "%Y-%m-%d_%H-%M-%S")
            try:
                return datetime.now().strftime(format_str)
            except Exception as e:
                print(f"Warning: Invalid datetime format '{format_str}': {e}")
                return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        elif var_type == "timestamp":
            return str(int(datetime.now().timestamp()))

        elif var_type == "clipboard":
            try:
                return pyperclip.paste()
            except Exception as e:
                print(f"Warning: Failed to get clipboard: {e}")
                return ""

        else:
            print(f"Warning: Unknown variable type '{var_type}' for ${var_name}")
            return default

    def _prompt_file_picker(self, var_config: Dict, default: str) -> Optional[str]:
        """Show file picker dialog"""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        prompt = var_config.get("prompt", "Select a file")
        initial_dir = Path(default).parent if default and Path(default).exists() else None

        result = filedialog.askopenfilename(
            title=prompt,
            initialdir=initial_dir,
            initialfile=Path(default).name if default else ""
        )

        root.destroy()

        return result if result else (default if default else None)

    def _prompt_folder_picker(self, var_config: Dict, default: str) -> Optional[str]:
        """Show folder picker dialog"""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        prompt = var_config.get("prompt", "Select a folder")
        initial_dir = default if default and Path(default).exists() else None

        result = filedialog.askdirectory(
            title=prompt,
            initialdir=initial_dir
        )

        root.destroy()

        return result if result else (default if default else None)

    def _prompt_input(self, var_config: Dict, default: str) -> Optional[str]:
        """Show text input dialog"""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        prompt = var_config.get("prompt", "Enter value")

        result = simpledialog.askstring(
            "Input Required",
            prompt,
            initialvalue=default,
            parent=root
        )

        root.destroy()

        return result if result is not None else (default if default else None)

    def reset(self):
        """Clear all resolved values"""
        self.resolved_values = {}
