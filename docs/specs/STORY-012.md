# STORY-012: Incremental Update Command (`pactkit-codex update`)

| Field | Value |
|-------|-------|
| ID | STORY-012 |
| Status | Done |
| Priority | P2 (Impact 3 / Effort 3) |
| Release | 0.2.0 |
| Depends | STORY-010 (dual-file), STORY-011 (rule loading) |

## Background

Currently `pactkit-codex init` performs a full deployment every time. When pactkit-codex is upgraded (e.g., new rules, updated prompts), users must re-run `init` which:

1. **Overwrites config.toml** — loses user customizations (model, MCP servers)
2. **No version tracking** — no way to know if deployed files are stale
3. **Redundant work** — re-deploys unchanged files

A dedicated `update` command enables safe, incremental upgrades that preserve user settings.

## Requirements

### R1: Version tracking in deployed files (MUST)

Write a version marker to `~/.codex/.pactkit-version` on every deploy:

```
0.1.0
```

The `update` command reads this to determine if upgrade is needed.

### R2: Skip if already current (MUST)

If deployed version matches installed version, print message and exit:

```
✅ Already up to date (v0.1.0)
```

### R3: Update PactKit-managed files only (MUST)

On upgrade, regenerate these files (PactKit-managed, safe to overwrite):

| Path | Action |
|------|--------|
| `~/.codex/AGENTS.md` | Regenerate |
| `~/.codex/rules/*.md` | Regenerate all |
| `~/.codex/prompts/*.md` | Regenerate all |
| `~/.codex/skills/*/SKILL.md` | Regenerate |
| `~/.codex/skills/*/scripts/*.py` | Regenerate |
| `./AGENTS.md` (project root) | Regenerate |

### R4: Preserve user-owned files (MUST)

These files MUST NOT be modified during update:

| Path | Reason |
|------|--------|
| `~/.codex/config.toml` | User API keys, model preferences |
| `.codex/AGENTS.local.md` | User project instructions |
| `.codex/pactkit.yaml` | User project config |

### R5: Merge config.toml additively (SHOULD)

If new PactKit version introduces new config keys (e.g., new MCP server), add them without removing existing user keys. Use the same merge logic as `init`.

### R6: `--force` flag to bypass version check (SHOULD)

Allow `pactkit-codex update --force` to re-deploy even if versions match. Useful for:
- Recovering corrupted files
- Re-deploying after manual edits to managed files

### R7: `--if-needed` flag for CI/automation (MUST)

`pactkit-codex update --if-needed` is a no-op if already current (exit 0, no output). This is used in session hooks:

```markdown
## Session Context
On new session, run `pactkit-codex update --if-needed` to sync files if upgraded.
```

### R8: Dry-run mode (SHOULD)

`pactkit-codex update --dry-run` shows what would be updated without making changes:

```
Would update:
  ~/.codex/AGENTS.md (0.1.0 → 0.2.0)
  ~/.codex/rules/01-core-protocol.md
  ~/.codex/prompts/project-act.md
  ...
Preserved (user-owned):
  ~/.codex/config.toml
  .codex/AGENTS.local.md
```

## Acceptance Criteria

### AC1: Version file created on init

- **Given** a fresh `pactkit-codex init`
- **When** deployment completes
- **Then** `~/.codex/.pactkit-version` exists and contains the version string

### AC2: Update skips if current

- **Given** deployed version matches installed version
- **When** running `pactkit-codex update`
- **Then** prints "Already up to date" and exits 0

### AC3: Update regenerates managed files

- **Given** deployed version is older than installed
- **When** running `pactkit-codex update`
- **Then** AGENTS.md, rules/, prompts/, skills/ are regenerated
- **And** `~/.codex/.pactkit-version` is updated to new version

### AC4: Update preserves user files

- **Given** user has customized `config.toml` and `AGENTS.local.md`
- **When** running `pactkit-codex update`
- **Then** those files are unchanged

### AC5: --force bypasses version check

- **Given** deployed version equals installed version
- **When** running `pactkit-codex update --force`
- **Then** all managed files are regenerated anyway

### AC6: --if-needed is silent when current

- **Given** deployed version matches installed version
- **When** running `pactkit-codex update --if-needed`
- **Then** exits 0 with no output

### AC7: --dry-run shows plan without changes

- **Given** an outdated deployment
- **When** running `pactkit-codex update --dry-run`
- **Then** lists files that would change
- **And** no files are actually modified

## Implementation Notes

### CLI changes (cli.py)

Add `update` subcommand:

```python
@app.command()
def update(
    force: bool = typer.Option(False, "--force", help="Bypass version check"),
    if_needed: bool = typer.Option(False, "--if-needed", help="Silent no-op if current"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show plan without changes"),
):
    ...
```

### deployer.py changes

1. Add `_write_version_marker(codex_root)` — called at end of `_deploy_codex()`
2. Add `_read_deployed_version(codex_root)` — returns version string or None
3. Add `update(force=False, if_needed=False, dry_run=False)` — main update logic
4. Refactor `_deploy_codex()` to accept `skip_user_files=False` flag for update mode

### Version comparison

Use simple string comparison (semver not required for MVP):

```python
from pactkit_codex import __version__

deployed = _read_deployed_version(codex_root)
if deployed == __version__ and not force:
    if not if_needed:
        print(f"✅ Already up to date (v{__version__})")
    return
```

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 Credential safety | Yes | MUST NOT read/write API keys from config.toml |
| SEC-2 Path traversal | No | Writes to fixed paths only |
| SEC-3 Config isolation | Yes | MUST NOT modify user-owned files |

## Out of Scope

- Rollback to previous version (complex, low value)
- Per-file version tracking (overkill for MVP)
- Automatic update check on session start (requires network)
