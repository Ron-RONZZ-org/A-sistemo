# AGENTS.md — Rules for A-sistemo
This file extends [A-workspace](./workspace/AGENTS.md).

This file extends root A-core AGENTS.md for the A-sistemo plugin.

## Project Overview

A-sistemo is a CLI plugin for system management (Wi-Fi, Bluetooth, USB, disk, trash).

## Relationship to A-core

**A-sistemo depends on A-core** for:
- `A` package for i18n (`tr()`), output (`error()`, `info()`), and subprocess (`run()`)
- Plugin discovery via entry points
- SQLite utilities when needed
- **API Reference**: See [A-core AGENTS.md](https://github.com/Ron-RONZZ-org/A-core/blob/main/AGENTS.md#api-reference)

All source code must import from `A`, not duplicate utilities.

## Architecture

```
src/A_sistemo/
├── __init__.py       # Plugin exports
├── cli/             # Typer apps (depends on A + Typer)
├── services/        # Business logic (depends on A)
└── data/           # SQLite (depends on A.data)
```

**Rule:** CLI → Service → Data → Core. No reverse dependencies.

## Code Standards

1. Import from `A` — never duplicate utilities
2. Use `tr()` for all user-facing strings
3. Use `error()` for errors, `info()` for info
4. Use `A.utils.run` for subprocess calls
5. Type hints on all public functions
6. Docstrings on all public functions
7. Tests required for all modules

## Testing

```bash
poetry run pytest tests/
```



## Package Manager: `uv` is Required

All A-ecosystem development **must** use `uv` as the package manager:

| Operation | Command |
|-----------|---------|
| Install dependencies | `uv pip install <pkg>` |
| Install project in dev mode | `uv pip install -e .` |
| Run tests | `uv run pytest tests/` |
| Install CLI tools (poetry, etc.) | `uv tool install <tool>` |
| Add dev dependency | `uv add --dev <pkg>` |

**Exceptions:**
- `pip` in README install instructions is acceptable for end users who may not have `uv`
- Readthedocs platform build may require `pip` (platform constraint)
- Runtime `install-on-confirmation` code may fall back to `pip` if `uv` is unavailable (see A-core AGENTS.md)

## What to Avoid

- Don't duplicate A-core utilities
- Don't skip i18n (use `tr()`)
- Don't use `print()` — use `A.utils.output`
- Don't hardcode command paths — use `shutil.which()` or `A.utils.run`

## Documentation

- **Readthedocs**: https://a-sistemo.readthedocs.io
- Supports multilingual: English, Esperanto, French

## Branch Convention
All A-* repos use `main` as the primary branch. Use `main` for all development.
