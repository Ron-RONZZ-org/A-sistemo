# A-sistemo

## Context

For architecture and API reference, see [A-workspace](./workspace/).

A-sistemo - System management commands

## Install

```bash
pip install A-sistemo
```

Requires **A-core** (automatically installed as dependency).

## Commands

```bash
A sistemo           # Show system info (default)
A sistemo info      # Show system info
A sistemo wifi ls   # List Wi-Fi networks
A sistemo bluhdento ls  # List Bluetooth devices
A sistemo usb ls   # List USB devices
A sistemo disko ls # List disk devices
A sistemo rubo ls  # List trash
```

## About

A-sistemo is a plugin for the [A](https://github.com/Ron-RONZZ-org/A-core/) framework.

**A-sistemo depends on A-core** for:
- Plugin discovery via entry points
- i18n (tr() for multilingual support)
- SQLite with WAL mode when needed
- Shared utilities (error(), info(), run())

See the [A-core documentation](https://github.com/Ron-RONZZ-org/A-core/) for more on the framework.

## Plugins

A-sistemo includes multiple subcommands:

| Command | Description |
|---------|-------------|
| wifi | Wi-Fi management |
| bluhdento | Bluetooth management |
| usb | USB device listing |
| disko | Disk device listing |
| rubo | Trash management |
| sxelo-aliaso | Bash alias management |
| particio | Partition management |

## License

GPL-3.0-only