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

## CLI Option Naming Conventions

All CLI option names (long flags) **must be in Esperanto**:

```python
# ✅ CORRECT
def modifi(uid: int, dosiero: Optional[Path] = typer.Option(None, "-D", "--dosiero", ...)):
```

| Rule | Example | Explanation |
|------|---------|-------------|
| Long name in Esperanto | `--dosiero` not `--file` | User-facing names are Esperanto |
| Python param in English | `file_path:` not `dosiero:` | Source code is English |
| Short flag avoids conflicts | `-D` not `-d` | `-d` is reserved for `--difino` etc. across A-ecosystem |

### Short Flag Priority

When choosing a short flag for an Esperanto option:

1. **Lowercase first letter** (e.g. `-f` for `--funkcio`) — preferred
2. **Uppercase** (e.g. `-D` for `--dosiero`) — when the lowercase letter conflicts with a common A-ecosystem convention (`-d/--difino`, `-l/--lingvo`, `-t/--titolo`, etc.)
3. **`-h` reserved for `--help`** — never use for other options

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

### Editable Install (Development Workflow)

After making changes to source files, the changes are only visible to `A` commands if the module is installed in **editable mode**. If you get "No such command" errors after adding a new command:

1. **Check install mode** - verify the module is editable:
   ```bash
   python -c "import A_sistemo; print(A_sistemo.__file__)"
   # Expected: .../A-sistemo/src/A_sistemo/__init__.py  (source)
   # NOT:     .../site-packages/A_sistemo/__init__.py    (stale copy)
   ```

2. **Reinstall as editable** from the workspace root:
   ```bash
   cd ~/kodo/autish
   uv pip install -e ~/kodo/autish/A-sistemo/
   ```

3. **Verify** the command is registered:
   ```bash
   A sistemo --help | grep espanso
   ```

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
