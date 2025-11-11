"""
App Configuration Wizard - Create app configs easily
"""
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import json
import sys
import os

# Import from parent directory for venv detection and env parsing
sys.path.insert(0, str(Path(__file__).parent.parent))
from venv_detector import detect_venv
from env_parser import find_env_files


class AppWizard(tk.Toplevel):
    """Wizard for creating app configurations"""

    def __init__(self, parent, config_dir: Path, on_complete_callback=None):
        super().__init__(parent)

        self.config_dir = config_dir
        self.on_complete_callback = on_complete_callback

        self.title("Add App to Launcher")
        self.geometry("600x550")

        # App configuration data
        self.selected_script = None
        self.selected_venv = None
        self.selected_icon = None
        self.selected_env_files = []
        self.selected_env_directory = None

        # Make window appear on top initially
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))

        self._create_widgets()
        self.center_window()

    def center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _create_widgets(self):
        """Create the UI widgets"""
        # App Name
        tk.Label(self, text="App Name:", font=("Arial", 10, "bold")).pack(pady=(10, 5))

        name_frame = tk.Frame(self)
        name_frame.pack(fill=tk.X, padx=20, pady=5)

        self.name_entry = tk.Entry(name_frame)
        self.name_entry.pack(fill=tk.X)

        # Script selection
        tk.Label(self, text="Python Script:", font=("Arial", 10, "bold")).pack(pady=(20, 5))

        script_frame = tk.Frame(self)
        script_frame.pack(fill=tk.X, padx=20, pady=5)

        self.script_label = tk.Label(script_frame, text="No script selected", fg="gray")
        self.script_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(script_frame, text="Browse...", command=self.select_script).pack(side=tk.RIGHT)

        # Venv selection
        tk.Label(self, text="Virtual Environment (optional):", font=("Arial", 10, "bold")).pack(pady=(20, 5))

        venv_frame = tk.Frame(self)
        venv_frame.pack(fill=tk.X, padx=20, pady=5)

        self.venv_label = tk.Label(venv_frame, text="No venv detected", fg="gray")
        self.venv_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(venv_frame, text="Change...", command=self.select_venv).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(venv_frame, text="Clear", command=self.clear_venv).pack(side=tk.RIGHT)

        # Icon selection
        tk.Label(self, text="Icon (optional):", font=("Arial", 10, "bold")).pack(pady=(20, 5))

        icon_frame = tk.Frame(self)
        icon_frame.pack(fill=tk.X, padx=20, pady=5)

        self.icon_label = tk.Label(icon_frame, text="No icon (will auto-generate)", fg="gray")
        self.icon_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(icon_frame, text="Browse...", command=self.select_icon).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(icon_frame, text="Clear", command=self.clear_icon).pack(side=tk.RIGHT)

        # Environment files
        tk.Label(self, text="Environment Files (optional):", font=("Arial", 10, "bold")).pack(pady=(20, 5))

        env_frame = tk.Frame(self)
        env_frame.pack(fill=tk.X, padx=20, pady=5)

        self.env_label = tk.Label(env_frame, text="No env files configured", fg="gray")
        self.env_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(env_frame, text="Configure...", command=self.configure_env_files).pack(side=tk.RIGHT)

        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=30, padx=20, fill=tk.X)

        tk.Button(
            button_frame,
            text="Create Config",
            command=self.create_config,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            height=2
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy,
            font=("Arial", 12),
            height=2
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    def select_script(self):
        """Select Python script"""
        filepath = filedialog.askopenfilename(
            title="Select Python Script",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )

        if filepath:
            self.selected_script = Path(filepath)
            self.script_label.config(text=str(self.selected_script), fg="black")

            # Auto-fill name if empty
            if not self.name_entry.get():
                default_name = self.selected_script.stem.replace("_", " ").title()
                self.name_entry.insert(0, default_name)

            # Auto-detect venv
            detected_venv = detect_venv(self.selected_script)
            if detected_venv:
                self.selected_venv = detected_venv
                self.venv_label.config(text=str(detected_venv), fg="black")
            else:
                self.selected_venv = None
                self.venv_label.config(text="No venv detected", fg="gray")

            # Find .env files
            env_files = find_env_files(self.selected_script.parent)
            if env_files:
                self.selected_env_files = env_files
                self.update_env_label()

    def select_venv(self):
        """Select virtual environment"""
        dirpath = filedialog.askdirectory(
            title="Select Virtual Environment Directory"
        )

        if dirpath:
            venv_path = Path(dirpath)
            # Verify it's a valid venv
            if (venv_path / "Scripts" / "python.exe").exists():
                self.selected_venv = venv_path
                self.venv_label.config(text=str(venv_path), fg="black")
            else:
                messagebox.showerror("Invalid Venv", "Selected directory is not a valid virtual environment.")

    def clear_venv(self):
        """Clear venv selection"""
        self.selected_venv = None
        self.venv_label.config(text="No venv selected", fg="gray")

    def select_icon(self):
        """Select icon file"""
        filepath = filedialog.askopenfilename(
            title="Select Icon File",
            filetypes=[
                ("Image files", "*.png *.jpg *.ico"),
                ("All files", "*.*")
            ]
        )

        if filepath:
            self.selected_icon = Path(filepath)
            self.icon_label.config(text=str(self.selected_icon), fg="black")

    def clear_icon(self):
        """Clear icon selection"""
        self.selected_icon = None
        self.icon_label.config(text="No icon (will auto-generate)", fg="gray")

    def configure_env_files(self):
        """Configure environment files"""
        dialog = tk.Toplevel(self)
        dialog.title("Configure Environment Files")
        dialog.geometry("600x400")

        tk.Label(dialog, text="Environment File Configuration", font=("Arial", 12, "bold")).pack(pady=10)

        # Individual files
        files_frame = tk.LabelFrame(dialog, text="Individual Files", padx=10, pady=10)
        files_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        files_listbox = tk.Listbox(files_frame, height=6)
        files_listbox.pack(fill=tk.BOTH, expand=True)

        for env_file in self.selected_env_files:
            files_listbox.insert(tk.END, str(env_file))

        files_button_frame = tk.Frame(files_frame)
        files_button_frame.pack(pady=5)

        def add_file():
            filepath = filedialog.askopenfilename(
                title="Select Environment File",
                filetypes=[("Environment files", "*.env"), ("All files", "*.*")]
            )
            if filepath:
                env_file = Path(filepath)
                if env_file not in self.selected_env_files:
                    self.selected_env_files.append(env_file)
                    files_listbox.insert(tk.END, str(env_file))

        def remove_file():
            selection = files_listbox.curselection()
            if selection:
                index = selection[0]
                files_listbox.delete(index)
                self.selected_env_files.pop(index)

        tk.Button(files_button_frame, text="Add File", command=add_file).pack(side=tk.LEFT, padx=5)
        tk.Button(files_button_frame, text="Remove Selected", command=remove_file).pack(side=tk.LEFT, padx=5)

        # Directory
        dir_frame = tk.LabelFrame(dialog, text="Or Scan Directory", padx=10, pady=10)
        dir_frame.pack(fill=tk.X, padx=20, pady=10)

        dir_label = tk.Label(dir_frame, text=str(self.selected_env_directory) if self.selected_env_directory else "No directory selected", fg="gray" if not self.selected_env_directory else "black")
        dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def select_dir():
            dirpath = filedialog.askdirectory(title="Select Directory to Scan for .env Files")
            if dirpath:
                self.selected_env_directory = Path(dirpath)
                dir_label.config(text=str(self.selected_env_directory), fg="black")

        def clear_dir():
            self.selected_env_directory = None
            dir_label.config(text="No directory selected", fg="gray")

        tk.Button(dir_frame, text="Browse...", command=select_dir).pack(side=tk.RIGHT, padx=(5, 0))
        tk.Button(dir_frame, text="Clear", command=clear_dir).pack(side=tk.RIGHT)

        # Done button
        def done():
            self.update_env_label()
            dialog.destroy()

        tk.Button(dialog, text="Done", command=done, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(pady=10)

    def update_env_label(self):
        """Update the environment files label"""
        count = len(self.selected_env_files)
        if self.selected_env_directory:
            if count > 0:
                self.env_label.config(text=f"{count} files + directory scan", fg="black")
            else:
                self.env_label.config(text="Directory scan configured", fg="black")
        elif count > 0:
            self.env_label.config(text=f"{count} file(s) configured", fg="black")
        else:
            self.env_label.config(text="No env files configured", fg="gray")

    def create_config(self):
        """Create the configuration file"""
        # Validate
        app_name = self.name_entry.get().strip()
        if not app_name:
            messagebox.showerror("Error", "Please enter an app name.")
            return

        if not self.selected_script:
            messagebox.showerror("Error", "Please select a Python script.")
            return

        # Build config
        config = {
            "name": app_name,
            "script": str(self.selected_script).replace("\\", "/")
        }

        if self.selected_icon:
            config["icon"] = str(self.selected_icon).replace("\\", "/")

        if self.selected_venv:
            config["venv"] = str(self.selected_venv).replace("\\", "/")

        if self.selected_env_files:
            config["env_files"] = [str(f).replace("\\", "/") for f in self.selected_env_files]

        if self.selected_env_directory:
            config["env_directory"] = str(self.selected_env_directory).replace("\\", "/")

        # Generate config filename from app name
        config_filename = app_name.lower().replace(" ", "_") + ".json"
        config_path = self.config_dir / config_filename

        # Check if exists
        if config_path.exists():
            if not messagebox.askyesno("File Exists", f"{config_filename} already exists. Overwrite?"):
                return

        # Write config
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            messagebox.showinfo("Success", f"Configuration created!\n\n{config_path}\n\nClick 'Reload Configs' in the launcher menu to see your new app.")

            # Call callback
            if self.on_complete_callback:
                self.on_complete_callback()

            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create config:\n{str(e)}")
