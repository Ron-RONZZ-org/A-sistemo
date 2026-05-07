# A-sistemo Documentation

 Welcome to A-sistemo — system management commands for A framework.

## Quick Start

### Installation

 ```bash
 pip install A-sistemo
 ```

 Or from source:

 ```bash
 git clone https://github.com/Ron-RONZZ-org/A-sistemo.git
 cd A-sistemo
 poetry install
 ```

### Basic Usage

 ```bash
 A sistemo --help           # Show help
 A sistemo help            # Show help
 A sistemo ls             # List all subcommands
 ```

### Installing

 ```bash
 pip install A-sistemo  # Requires A-core
 ```

---

## Commands

A-sistemo provides system management commands:

| Command | Description |
|---------|-------------|
| `info` | System information |
| `wifi` | Wi-Fi management |
| `bluhdento` | Bluetooth management |
| `usb` | USB devices |
| `disko` | Disk devices |
| `particio` | Partition management |
| `rubo` | Trash management |
| `selo-aliaso` | Bash alias management |

### System Info

 ```bash
 A sistemo info      # Show system information
 ```

 Shows: OS, hostname, kernel, uptime, CPU, memory, disk.

### Wi-Fi

 ```bash
 A sistemo wifi ls           # List Wi-Fi networks
 A sistemo wifi konekti SSID  # Connect to network
 A sistemo wifi forigi SSID  # Remove saved network
 ```

### Bluetooth

 ```bash
 A sistemo bluhdento ls        # List Bluetooth devices
 A sistemo bluhdento serci    # Search for devices
 ```

### USB

 ```bash
 A sistemo usb ls           # List USB devices
 A sistemo usb detaloj ID   # Show device details
 ```

### Disk

 ```bash
 A sistemo disko ls        # List disk devices
 A sistemo disko detaloj   # Show disk details
 ```

### Partitions

 ```bash
 A sistemo particio ls      # List partitions
 A sistemo particio detaloj # Show partition details
 ```

### Trash

 ```bash
 A sistemo rubo ls          # List trash
 A sistemo ruboelten      # Empty trash
 A sistemo rubo grandeco   # Show trash size
 ```

### Bash Aliases

 ```bash
 A sistemo selo-aliaso ls        # List aliases
 A sistemo selo-aliaso aldoni   # Add alias
 A sistemo selo-aliaso forigi    # Remove alias
 ```

---

## Architecture

A-sistemo has a simple two-layer architecture:

 ```
 ┌─────────────────────────────────────────────┐
 │ CLI Layer (Typer)                          │
 │ Commands, argument parsing                 │
 ├─────────────────────────────────────────────┤
 │ Service Layer                             │
 │ Business logic                           │
 └─────────────────────────────────────────────┘
 ```

 No SQLite —system commands only.

---

## Dependencies

A-sistemo depends on A-core:

 ```python
 from A import tr, error, info, run
 ```

---

## Migration from Autish

See [README](../README.md).

---

## Contributing

Please see CONTRIBUTING.md in the repository root.

---

## License

GPL-3.0-only