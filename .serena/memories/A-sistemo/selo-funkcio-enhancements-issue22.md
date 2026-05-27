# Issue #22 - A-sistemo selo-funkcio enhancements

## Problem Summary
Three issues with `selo-funkcio aldoni`:
1. Tilde `~` not expanded in file path
2. On duplicate function name, should offer to update (like A-encik does)
3. Should support importing multiple functions from same file

## Solution Design (2026-05-27) — COMPLETED

**Status: COMPLETED** — implemented in commit 27a6f6e, merged to `main`.

## Files changed
| File | Change |
|------|--------|
| `src/A_sistemo/services/bash_function_db.py` | Added `parse_functions_from_file()` (+40 lines) |
| `src/A_sistemo/services/__init__.py` | Added exports for `parse_function_file`, `parse_functions_from_file`, `validate_bash_syntax` |
| `src/A_sistemo/cli/bash_function.py` | Rewrote `aldoni` as multi-function loop; added `_resolve_path()` helper; fixed tilde in `modifi`; added `--jes` flag |
| `tests/test_bash_function_db.py` | 23 new tests (new file) |
| `docs/en/index.md`, `docs/eo/index.md`, `docs/fr/index.md` | Added `selo-funkcio` to command tables + usage sections |
| `README.md` | Added `selo-funkcio` to command table |

## Verification
- 43 tests pass (23 new + 20 existing)
- User-simulation tests passed (tilde expansion, multi-function, duplicate update)
- Issue #22 closed
Architect-approved plan:

### Problem 1: Tilde expansion
- Remove `exists=True`/`readable=True` from Typer Argument/Option
- Validate manually after `expanduser().resolve()`
- Affects: `aldoni` and `modifi` commands

### Problem 2: Duplicate → propose update
- Replace error with `typer.prompt("Ĉu ĝisdatigi? (J/n)")`
- Pattern matches A-encik duplicate handling
- Add `--jes`/`-y` flag for auto-confirm

### Problem 3: Multiple functions per file
- New `parse_functions_from_file()` using `re.findall()`
- `aldoni` becomes a loop over parsed functions
- Keep `parse_function_file()` for `modifi` backward compatibility
- Validate ALL functions before inserting (fail-fast)
- Single `sync_shell_config()` call after all ops

### Files to change
- `services/bash_function_db.py`: +40 lines (new parse function)
- `services/__init__.py`: +1 line (export)
- `cli/bash_function.py`: ~50 lines modified (aldoni rewrite, tilde fixes)
