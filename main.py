"""
Python App Launcher - System tray application
"""
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys
import os
import threading
from typing import Optional, List

import pystray
from PIL import Image, ImageDraw, ImageFont
from config_loader import ConfigLoader, AppConfig
from menu_builder import MenuBuilder
from app_wizard import AppWizard
from startup_manager import StartupManager


class LauncherApp:
    """Main launcher application with system tray icon"""

    def __init__(self):
        # Get config directory (relative to this script)
        self.base_dir = Path(__file__).parent
        self.config_dir = self.base_dir / "configs"

        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)

        # Load configurations
        self.config_loader = ConfigLoader(self.config_dir)
        self.all_configs = []
        self.reload_configs()

        # Menu builder
        self.menu_builder = MenuBuilder(on_launch_callback=self.on_app_launched)

        # Startup manager
        self.startup_manager = StartupManager(Path(__file__))

        # System tray icon
        self.icon = None

        # Create hidden root window for tkinter
        self.root = tk.Tk()
        self.root.withdraw()

        # Cache for loaded icon images
        self.icon_cache = {}

    def reload_configs(self):
        """Reload all configurations"""
        self.all_configs = self.config_loader.load_all_configs()
        print(f"Loaded {len(self.all_configs)} app configurations")

    def on_app_launched(self, app_config: AppConfig):
        """Callback when an app is successfully launched"""
        print(f"Launched: {app_config.name}")

    def create_icon_image(self):
        """Create a simple icon image for the system tray"""
        # Create a 64x64 image with a Python-style icon
        width = 64
        height = 64
        color1 = (52, 101, 164)  # Python blue
        color2 = (255, 212, 59)  # Python yellow

        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)

        # Draw a simple "Py" symbol
        dc.ellipse([8, 8, 28, 28], fill=color2)
        dc.ellipse([36, 36, 56, 56], fill=color2)

        return image

    def generate_initial_icon(self, app_name: str):
        """Generate an icon with the app's initial"""
        # Use app name to generate consistent color
        color_hash = hash(app_name)

        # Color palette (various nice colors)
        colors = [
            (100, 180, 255),  # Blue
            (80, 200, 120),   # Green
            (255, 140, 100),  # Orange
            (200, 100, 200),  # Purple
            (255, 180, 100),  # Yellow-orange
            (100, 200, 200),  # Cyan
            (255, 120, 150),  # Pink
            (150, 100, 200),  # Indigo
            (200, 180, 80),   # Gold
            (120, 180, 100),  # Lime
        ]

        # Pick color based on hash
        bg_color = colors[color_hash % len(colors)]

        # Get initial
        initial = app_name[0].upper() if app_name else "?"

        # Create 24x24 icon
        img = Image.new('RGB', (24, 24), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Draw initial in white with larger font
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()

        # Center the text
        bbox = draw.textbbox((0, 0), initial, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (24 - text_width) // 2
        y = (24 - text_height) // 2 - 2

        draw.text((x, y), initial, fill=(255, 255, 255), font=font)

        return img

    def load_icon(self, icon_path: Path, app_name: str = ""):
        """Load an icon and convert to PhotoImage for menu use"""
        # Check cache first
        cache_key = str(icon_path) if icon_path else f"generated_{app_name}"
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        try:
            from PIL import ImageTk

            if icon_path and icon_path.exists():
                # Load and resize icon to 24x24 for menu
                img = Image.open(icon_path)
                img = img.resize((24, 24), Image.Resampling.LANCZOS)
            else:
                # Generate icon from initial
                img = self.generate_initial_icon(app_name)

            photo = ImageTk.PhotoImage(img)

            # Cache it
            self.icon_cache[cache_key] = photo
            return photo
        except Exception as e:
            print(f"Warning: Failed to load/generate icon: {e}")
            return None

    def show_launcher_menu(self, icon=None, item=None):
        """Show the launcher menu (like Windows Start menu)"""
        # Create a popup menu at mouse cursor position
        menu = tk.Menu(self.root, tearoff=0)

        # Add header
        menu.add_command(label="▼ APPLICATIONS", state="disabled")
        menu.add_separator()

        # Add each app to the menu
        for app_config in self.all_configs:
            # Load icon (from file if available, otherwise generate from initial)
            icon_image = self.load_icon(app_config.icon, app_config.name)

            # Get menu flow to determine if we need submenus
            flow = self.menu_builder.get_menu_flow(app_config)

            if flow == "direct":
                # Simple menu item that launches directly
                menu.add_command(
                    label=app_config.name,
                    image=icon_image,
                    compound='left',
                    command=lambda ac=app_config: self.menu_builder.launch_app_with_config(ac)
                )
            else:
                # Add cascading submenu
                submenu = self._build_app_submenu(app_config, flow)
                menu.add_cascade(label=app_config.name, image=icon_image, compound='left', menu=submenu)

        # Add separator and options submenu
        menu.add_separator()

        # Create Options submenu
        options_menu = tk.Menu(menu, tearoff=0)
        options_menu.add_command(label="Add App...", command=lambda: self.show_add_app_wizard())
        options_menu.add_command(label="Open Config Directory", command=lambda: self.open_config_directory())
        options_menu.add_command(label="Reload Configs", command=lambda: self.reload_menu_action())

        # Dynamic startup menu item
        startup_label = "Remove from Startup" if self.startup_manager.is_in_startup() else "Add to Startup"
        options_menu.add_command(label=startup_label, command=lambda: self.toggle_startup())

        menu.add_cascade(label="Options", menu=options_menu)

        menu.add_separator()
        menu.add_command(label="Quit", command=lambda: self.quit_app())

        # Show menu at mouse position
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()

    def _build_app_submenu(self, app_config: AppConfig, flow: str):
        """Build cascading submenu for an app"""
        submenu = tk.Menu(self.root, tearoff=0)

        if flow == "env_only":
            # Add header
            submenu.add_command(label="▼ ENVIRONMENT", state="disabled")
            submenu.add_separator()

            # Show env file options
            env_items = self.menu_builder.build_env_menu_items(app_config)
            for display_name, env_file in env_items:
                submenu.add_command(
                    label=display_name,
                    command=lambda ef=env_file: self.menu_builder.launch_app_with_config(
                        app_config, env_file=ef
                    )
                )

        elif flow == "param_only":
            # Add header
            submenu.add_command(label="▼ PARAMETERS", state="disabled")
            submenu.add_separator()

            # Show parameter set options
            param_items = self.menu_builder.build_param_menu_items(app_config)
            for display_name, param_set in param_items:
                submenu.add_command(
                    label=display_name,
                    command=lambda ps=param_set: self.menu_builder.launch_app_with_config(
                        app_config, param_set=ps
                    )
                )

        else:  # env_then_param
            # Add header
            submenu.add_command(label="▼ ENVIRONMENT", state="disabled")
            submenu.add_separator()

            # Show env options, each with param submenus
            env_items = self.menu_builder.build_env_menu_items(app_config)
            for display_name, env_file in env_items:
                # Create submenu for this env option
                env_submenu = tk.Menu(submenu, tearoff=0)

                # Add header to param submenu
                env_submenu.add_command(label="▼ PARAMETERS", state="disabled")
                env_submenu.add_separator()

                param_items = self.menu_builder.build_param_menu_items(app_config)
                for param_name, param_set in param_items:
                    env_submenu.add_command(
                        label=param_name,
                        command=lambda ef=env_file, ps=param_set: self.menu_builder.launch_app_with_config(
                            app_config, env_file=ef, param_set=ps
                        )
                    )

                submenu.add_cascade(label=display_name, menu=env_submenu)

        return submenu

    def show_add_app_wizard(self, icon=None, item=None):
        """Show the add app wizard"""
        wizard = AppWizard(self.root, self.config_dir, on_complete_callback=self.reload_configs)

    def open_config_directory(self, icon=None, item=None):
        """Open the configs directory in file explorer"""
        os.startfile(self.config_dir)

    def reload_menu_action(self, icon=None, item=None):
        """Reload configurations"""
        self.reload_configs()
        print("Configurations reloaded")

    def toggle_startup(self, icon=None, item=None):
        """Toggle launcher in Windows startup"""
        if self.startup_manager.is_in_startup():
            # Remove from startup
            if self.startup_manager.remove_from_startup():
                print("Removed from startup")
                from tkinter import messagebox
                messagebox.showinfo("Startup", "Launcher removed from Windows startup")
            else:
                from tkinter import messagebox
                messagebox.showerror("Error", "Failed to remove from startup")
        else:
            # Add to startup
            if self.startup_manager.add_to_startup():
                print("Added to startup")
                from tkinter import messagebox
                messagebox.showinfo("Startup", "Launcher added to Windows startup")
            else:
                from tkinter import messagebox
                messagebox.showerror("Error", "Failed to add to startup")

    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        print("Quitting application...")

        # Schedule the actual quit on the tkinter thread to avoid pystray errors
        self.root.after(100, self._do_quit)

    def _do_quit(self):
        """Actually perform the quit (called from tkinter thread)"""
        # Stop the system tray icon
        if self.icon:
            self.icon.stop()

        # Destroy root window and quit
        self.root.destroy()

    def setup_system_tray(self):
        """Setup the system tray icon and menu"""
        icon_image = self.create_icon_image()

        # Dynamic startup menu item
        def get_startup_label(item):
            return "Remove from Startup" if self.startup_manager.is_in_startup() else "Add to Startup"

        menu = pystray.Menu(
            pystray.MenuItem("Open Launcher", self.show_launcher_menu, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Add App...", self.show_add_app_wizard),
            pystray.MenuItem("Open Config Directory", self.open_config_directory),
            pystray.MenuItem("Reload Configs", self.reload_menu_action),
            pystray.MenuItem(get_startup_label, self.toggle_startup),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app)
        )

        self.icon = pystray.Icon(
            "python_launcher",
            icon_image,
            "Python App Launcher",
            menu
        )

    def run_icon(self):
        """Run the system tray icon (in separate thread)"""
        self.icon.run()

    def run(self):
        """Run the application"""
        self.setup_system_tray()
        print("Python App Launcher started")
        print(f"Config directory: {self.config_dir}")

        # Run pystray in a separate thread
        icon_thread = threading.Thread(target=self.run_icon, daemon=True)
        icon_thread.start()

        # If no configs exist, show the wizard
        if len(self.all_configs) == 0:
            print("No configs found - opening wizard...")
            self.root.after(500, self.show_add_app_wizard)

        # Run tkinter main loop in main thread
        self.root.mainloop()


def main():
    """Main entry point"""
    app = LauncherApp()
    app.run()


if __name__ == "__main__":
    main()
