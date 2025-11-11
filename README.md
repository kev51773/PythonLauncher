# Python App Launcher

A system tray application for launching Python scripts with configurable environments, parameters, and variables.

## Features

- **System Tray Integration**: Quick access from the Windows system tray
- **Smart Menu Navigation**: Only shows relevant menus (env files, parameters)
- **Environment File Support**: Load multiple .env files or scan directories
- **Variable System**: Dynamic prompts for file pickers, folder pickers, text input, dates, and clipboard
- **Detached Processes**: Apps run independently from the launcher
- **Custom Ordering**: Optional master config for custom app order
- **Virtual Environment Support**: Run apps in their configured venvs

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the launcher:
```bash
python main.py
```

2. The app will appear in your system tray (Python icon)

3. Right-click the tray icon to:
   - Select any configured app to launch
   - **Open Config Directory**: Open the configs folder to edit/add configs
   - **Reload Configs**: Reload after making config changes
   - **Quit**: Exit the launcher

4. When launching an app:
   - Select from environment files (if configured)
   - Select from parameter sets (if configured)
   - Apps launch in detached processes

## Configuration

### App Config Files

Create JSON files in the `configs/` directory. Each file represents one app.

**Example: `configs/my_app.json`**
```json
{
  "name": "My App",
  "script": "C:/projects/myapp/app.py",
  "icon": "C:/projects/myapp/icon.ico",
  "venv": "C:/projects/myapp/venv",
  "working_directory": "C:/projects/myapp",
  "description": "My awesome application",

  "env_files": ["config.env"],
  "env_directory": "C:/projects/myapp/envs",

  "variables": {
    "inputfile": {
      "type": "filepicker",
      "prompt": "Choose input file",
      "default": "C:/default.txt"
    },
    "outputdir": {
      "type": "folderpicker",
      "prompt": "Select output directory"
    },
    "mode": {
      "type": "input",
      "prompt": "Enter mode (auto/manual)",
      "default": "auto"
    }
  },

  "parameter_sets": [
    {
      "name": "Process File",
      "params": "--input=$inputfile --output=$outputdir --mode=$mode"
    },
    {
      "name": "Quick Run",
      "params": ""
    }
  ]
}
```

### Config Fields

#### Required
- `name`: Display name for the app
- `script`: Path to the Python script

#### Optional
- `icon`: Path to icon file (.ico, .exe, .dll)
- `venv`: Path to virtual environment
- `working_directory`: Working directory (defaults to script directory)
- `description`: Description shown in search results

#### Environment Files
- `env_files`: List of specific .env file paths
- `env_directory`: Directory to scan for .env files
- Both can be used together (they merge)

#### Variables
Define reusable variables with prompts:

**Variable Types:**
- `filepicker`: File selection dialog
- `folderpicker`: Folder selection dialog
- `input`: Text input dialog
- `datetime`: Current date/time with custom format (uses Python strftime format)
- `timestamp`: Unix timestamp (seconds since epoch)
- `clipboard`: Current clipboard content

**Variable Fields:**
- `type`: Variable type (required)
- `prompt`: Prompt text for dialogs (optional, for filepicker/folderpicker/input)
- `default`: Default value (optional, for filepicker/folderpicker/input)
- `format`: Format string for datetime (optional, Python strftime format)

**Common datetime formats:**
```json
{
  "type": "datetime",
  "format": "%Y-%m-%d"           // 2025-11-10
}
{
  "type": "datetime",
  "format": "%Y%m%d_%H%M%S"      // 20251110_143022
}
{
  "type": "datetime",
  "format": "%B %d, %Y"          // November 10, 2025
}
{
  "type": "datetime",
  "format": "%Y-%m-%d %H:%M:%S"  // 2025-11-10 14:30:22
}
```
See [Python strftime reference](https://strftime.org/) for all format codes.

#### Parameter Sets
Define named sets of command-line parameters. Use `$variable` to reference variables.

```json
"parameter_sets": [
  {
    "name": "Display Name",
    "params": "--arg1=value --arg2=$variable"
  }
]
```

### Master Config (Optional)

Create `configs/master.json` to define custom app ordering:

```json
{
  "order": [
    "my_app",
    "another_app",
    "third_app"
  ]
}
```

Apps not listed will appear alphabetically after the ordered ones.

## Menu Flow

The launcher automatically determines the menu flow based on configuration:

1. **No env, no params**: Launch directly
2. **Env only**: Show env menu → Launch
3. **Params only**: Show param menu → Launch
4. **Both**: Show env menu → Show param menu → Launch

## Examples

### Simple App (Direct Launch)
```json
{
  "name": "Quick Script",
  "script": "C:/scripts/quick.py"
}
```
Clicks directly launch the app.

### App with Env Files
```json
{
  "name": "Configured App",
  "script": "C:/scripts/app.py",
  "env_directory": "C:/scripts/envs"
}
```
Shows menu with env files, then launches.

### App with Variables
```json
{
  "name": "File Processor",
  "script": "C:/scripts/process.py",
  "variables": {
    "input": {"type": "filepicker", "prompt": "Choose file"}
  },
  "parameter_sets": [
    {"name": "Process", "params": "--file=$input"}
  ]
}
```
Shows param menu, prompts for file, then launches.

## Tips

- Right-click system tray icon to access all apps
- Reload configs after making changes (no need to restart)
- Keep config files simple - only include fields you need
- Use master.json to customize app ordering in the menu
