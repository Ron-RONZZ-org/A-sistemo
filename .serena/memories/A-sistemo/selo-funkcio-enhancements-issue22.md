# Issue #22 - A-sistemo selo-funkcio enhancements

## Problem Summary
Three issues with `selo-funkcio aldoni`:
1. Tilde `~` not expanded in file path
2. On duplicate function name, should offer to update (like A-encik does)
3. Should support importing multiple functions from same file

## Solution Design (2026-05-27)
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
