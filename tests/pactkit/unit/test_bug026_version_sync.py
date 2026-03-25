"""
BUG-026: Version Sync on Init/Update

Verify:
- R1: __version__ is importable in config.py
- R2: _rewrite_yaml() writes __version__, not the old value from user's yaml
- R3: auto_merge_config_file() syncs stale version to __version__
- AC1: version updated on init (stale -> current)
- AC2: version updated on update (older stale -> current)
- AC3: fresh-init yaml contains __version__
"""
from pathlib import Path

import yaml

from pactkit import __version__
from pactkit.config import (
    _rewrite_yaml,
    auto_merge_config_file,
    generate_default_yaml,
    get_default_config,
)

_STALE_V1 = "0.0.1"
_STALE_V2 = "1.4.0"


def _write_minimal(tmp_path: Path, version: str) -> Path:
    """Write a minimal pactkit.yaml with given version."""
    p = tmp_path / "pactkit.yaml"
    p.write_text(
        f'version: "{version}"\nstack: auto\nroot: .\n',
        encoding="utf-8",
    )
    return p


def _write_complete(tmp_path: Path, version: str) -> Path:
    """Write a complete pactkit.yaml (all sections) with given version."""
    cfg = get_default_config()
    cfg["version"] = version
    p = tmp_path / "pactkit.yaml"
    p.write_text(yaml.dump(cfg), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# R1: get_default_config uses __version__
# ---------------------------------------------------------------------------

class TestGetDefaultConfigVersion:
    """AC3 (partial): get_default_config() must return current __version__."""

    def test_version_equals_package_version(self):
        """get_default_config() version must match installed __version__."""
        cfg = get_default_config()
        assert cfg["version"] == __version__, (
            f"get_default_config() returned {cfg['version']!r}, expected {__version__!r}"
        )


# ---------------------------------------------------------------------------
# R2: _rewrite_yaml always writes __version__
# ---------------------------------------------------------------------------

class TestRewriteYamlVersion:
    """R2: _rewrite_yaml must use __version__, not the stale version from data."""

    def test_ignores_stale_version_in_data(self, tmp_path):
        """_rewrite_yaml must write __version__ even if data still has old version."""
        p = _write_minimal(tmp_path, _STALE_V1)
        data = yaml.safe_load(p.read_text())
        assert data["version"] == _STALE_V1  # pre-condition
        _rewrite_yaml(p, data)
        result = yaml.safe_load(p.read_text())
        assert result["version"] == __version__, (
            f"_rewrite_yaml preserved stale version {result['version']!r}; "
            f"expected {__version__!r}"
        )

    def test_upgrades_older_stale_version(self, tmp_path):
        """_rewrite_yaml must upgrade from any old version to __version__."""
        p = _write_minimal(tmp_path, _STALE_V2)
        data = yaml.safe_load(p.read_text())
        _rewrite_yaml(p, data)
        result = yaml.safe_load(p.read_text())
        assert result["version"] == __version__


# ---------------------------------------------------------------------------
# R3: auto_merge_config_file syncs stale version
# ---------------------------------------------------------------------------

class TestAutoMergeVersionSync:
    """R3: auto_merge_config_file must sync version to __version__."""

    def test_stale_version_updated_in_file(self, tmp_path):
        """AC1/AC2: after auto_merge, version in file must equal __version__."""
        p = _write_minimal(tmp_path, _STALE_V1)
        auto_merge_config_file(p)
        result = yaml.safe_load(p.read_text())
        assert result["version"] == __version__

    def test_older_stale_version_updated(self, tmp_path):
        """AC2: version "1.4.0" is updated to __version__ after auto_merge."""
        p = _write_minimal(tmp_path, _STALE_V2)
        auto_merge_config_file(p)
        result = yaml.safe_load(p.read_text())
        assert result["version"] == __version__

    def test_stale_version_reported_in_added(self, tmp_path):
        """auto_merge must report a version change in the returned added list."""
        p = _write_minimal(tmp_path, _STALE_V1)
        added = auto_merge_config_file(p)
        assert any("version" in item for item in added), (
            f"Expected version change in added list, got: {added}"
        )

    def test_current_version_not_reported_in_added(self, tmp_path):
        """No version change reported when yaml already has __version__."""
        p = _write_complete(tmp_path, __version__)
        added = auto_merge_config_file(p)
        assert not any("version" in item for item in added), (
            f"Unexpected version change in added list: {added}"
        )

    def test_complete_config_stale_version_still_synced(self, tmp_path):
        """R3: version sync fires even when all sections are present (nothing else to add)."""
        p = _write_complete(tmp_path, _STALE_V1)
        added = auto_merge_config_file(p)
        result = yaml.safe_load(p.read_text())
        assert result["version"] == __version__, (
            f"Version not synced for complete config; got {result['version']!r}"
        )
        assert any("version" in item for item in added), (
            f"Version change not reported in added list: {added}"
        )


# ---------------------------------------------------------------------------
# AC3: generate_default_yaml uses __version__
# ---------------------------------------------------------------------------

class TestGenerateDefaultYamlVersion:
    """AC3: generate_default_yaml() must output __version__ for fresh init."""

    def test_yaml_string_contains_package_version(self):
        """generate_default_yaml() must contain version: "__version__"."""
        yaml_str = generate_default_yaml()
        data = yaml.safe_load(yaml_str)
        assert data["version"] == __version__, (
            f"generate_default_yaml() wrote {data['version']!r}, expected {__version__!r}"
        )
