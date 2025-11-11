"""
Menu builder for app launcher navigation
"""
from pathlib import Path
from typing import List, Optional, Callable
from config_loader import AppConfig
from variable_resolver import VariableResolver
from app_launcher import launch_app


class MenuBuilder:
    """Builds and manages menu navigation logic"""

    def __init__(self, on_launch_callback: Optional[Callable] = None):
        """
        Initialize menu builder.

        Args:
            on_launch_callback: Optional callback to call after successful launch
        """
        self.on_launch_callback = on_launch_callback

    def launch_app_with_config(
        self,
        app_config: AppConfig,
        env_file: Optional[Path] = None,
        param_set: Optional[dict] = None
    ):
        """
        Launch an app with the given configuration.

        Args:
            app_config: The app configuration
            env_file: Selected environment file (optional)
            param_set: Selected parameter set dict with 'name' and 'params' (optional)
        """
        # Resolve parameters if needed
        params = ""
        if param_set:
            params = param_set.get("params", "")

            # Resolve variables in parameters
            if "$" in params:
                resolver = VariableResolver(app_config.variables)
                resolved_params = resolver.resolve_parameters(params)

                if resolved_params is None:
                    # User cancelled
                    return

                params = resolved_params

        # Prepare env files list
        env_files = []
        if env_file:
            env_files = [env_file]

        # Launch the app
        success = launch_app(
            script_path=app_config.script,
            parameters=params,
            venv_path=app_config.venv,
            env_files=env_files,
            working_directory=app_config.working_directory
        )

        if success and self.on_launch_callback:
            self.on_launch_callback(app_config)

    def should_show_env_menu(self, app_config: AppConfig) -> bool:
        """
        Determine if we should show the env selection menu.

        Returns:
            True if app has env files configured
        """
        env_files = app_config.get_all_env_files()
        return len(env_files) > 0

    def should_show_param_menu(self, app_config: AppConfig) -> bool:
        """
        Determine if we should show the parameter set menu.

        Returns:
            True if app has parameter sets configured
        """
        return len(app_config.parameter_sets) > 0

    def get_menu_flow(self, app_config: AppConfig) -> str:
        """
        Determine the menu flow for an app.

        Returns:
            One of: "direct", "env_only", "param_only", "env_then_param"
        """
        has_env = self.should_show_env_menu(app_config)
        has_param = self.should_show_param_menu(app_config)

        if not has_env and not has_param:
            return "direct"
        elif has_env and not has_param:
            return "env_only"
        elif not has_env and has_param:
            return "param_only"
        else:
            return "env_then_param"

    def build_env_menu_items(self, app_config: AppConfig) -> List[tuple]:
        """
        Build menu items for environment selection.

        Returns:
            List of (display_name, env_file_path) tuples
        """
        env_files = app_config.get_all_env_files()
        items = []

        # Add "No env file" option
        items.append(("No env file", None))

        # Add each env file
        for env_file in env_files:
            display_name = env_file.name
            items.append((display_name, env_file))

        return items

    def build_param_menu_items(self, app_config: AppConfig) -> List[tuple]:
        """
        Build menu items for parameter set selection.

        Returns:
            List of (display_name, param_set_dict) tuples
        """
        items = []

        for param_set in app_config.parameter_sets:
            name = param_set.get("name", "Unnamed")
            items.append((name, param_set))

        # If no parameter sets, add a default one
        if not items:
            items.append(("Run", {"name": "Run", "params": ""}))

        return items
