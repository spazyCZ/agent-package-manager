"""Unit tests for UAAPS v0.4.0/v0.5.0 manifest loading and model validation.

Tests for ``load_manifest_universal()`` and new ``PackageManifest`` fields
including structured permissions, prompts-to-commands migration, installMode,
and vendor extension validation.

Reference: tasks.md T076.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import json
import logging
from pathlib import Path

import pytest
import yaml

from pydantic import ValidationError

from aam_cli.core.manifest import (
    MAX_DESCRIPTION_LENGTH,
    ArtifactRef,
    ArtifactsDeclaration,
    EnvVarConfig,
    FsPermissions,
    NetworkPermissions,
    PackageManifest,
    PermissionsConfig,
    ShellPermissions,
    SystemDependencies,
    load_manifest_universal,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# HELPERS                                                                      #
#                                                                              #
################################################################################


def _write_json(path: Path, data: dict) -> None:
    """Write dict as JSON to path."""
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_yaml(path: Path, data: dict) -> None:
    """Write dict as YAML to path."""
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _minimal_manifest() -> dict:
    """Return a minimal valid manifest dict."""
    return {
        "name": "@test/pkg",
        "version": "1.0.0",
        "description": "Test package",
    }


################################################################################
#                                                                              #
# TESTS: load_manifest_universal                                               #
#                                                                              #
################################################################################


class TestLoadManifestUniversal:
    """Tests for ``load_manifest_universal()`` discovery logic."""

    def test_unit_load_json_only(self, tmp_path: Path) -> None:
        """JSON-only directory loads package.agent.json."""
        _write_json(tmp_path / "package.agent.json", _minimal_manifest())
        manifest = load_manifest_universal(tmp_path)
        assert manifest.name == "@test/pkg"
        assert manifest.manifest_format == "json"

    def test_unit_load_yaml_only(self, tmp_path: Path) -> None:
        """YAML-only directory loads package.agent.yaml."""
        _write_yaml(tmp_path / "package.agent.yaml", _minimal_manifest())
        manifest = load_manifest_universal(tmp_path)
        assert manifest.name == "@test/pkg"
        assert manifest.manifest_format == "yaml"

    def test_unit_load_legacy_only(self, tmp_path: Path) -> None:
        """Legacy-only directory loads aam.yaml."""
        _write_yaml(tmp_path / "aam.yaml", _minimal_manifest())
        manifest = load_manifest_universal(tmp_path)
        assert manifest.name == "@test/pkg"
        assert manifest.manifest_format == "legacy"

    def test_unit_json_wins_over_yaml(self, tmp_path: Path) -> None:
        """JSON takes precedence over YAML when both are present."""
        data_json = {**_minimal_manifest(), "version": "2.0.0"}
        data_yaml = {**_minimal_manifest(), "version": "1.0.0"}
        _write_json(tmp_path / "package.agent.json", data_json)
        _write_yaml(tmp_path / "package.agent.yaml", data_yaml)
        manifest = load_manifest_universal(tmp_path)
        assert manifest.version == "2.0.0"
        assert manifest.manifest_format == "json"

    def test_unit_json_wins_over_legacy(self, tmp_path: Path) -> None:
        """JSON takes precedence over aam.yaml legacy format."""
        data_json = {**_minimal_manifest(), "version": "3.0.0"}
        data_legacy = {**_minimal_manifest(), "version": "1.0.0"}
        _write_json(tmp_path / "package.agent.json", data_json)
        _write_yaml(tmp_path / "aam.yaml", data_legacy)
        manifest = load_manifest_universal(tmp_path)
        assert manifest.version == "3.0.0"
        assert manifest.manifest_format == "json"

    def test_unit_load_by_direct_file_path(self, tmp_path: Path) -> None:
        """Passing a file path directly loads that specific file."""
        json_path = tmp_path / "package.agent.json"
        _write_json(json_path, _minimal_manifest())
        manifest = load_manifest_universal(json_path)
        assert manifest.name == "@test/pkg"

    def test_unit_missing_all_raises_file_not_found(self, tmp_path: Path) -> None:
        """Empty directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_manifest_universal(tmp_path)

    def test_unit_max_description_length(self) -> None:
        """MAX_DESCRIPTION_LENGTH is 1024 characters (UAAPS v0.4.0)."""
        assert MAX_DESCRIPTION_LENGTH == 1024

    def test_unit_artifacts_field_optional(self, tmp_path: Path) -> None:
        """PackageManifest.artifacts is optional — no ValidationError when absent."""
        data = _minimal_manifest()
        # No 'artifacts' key at all
        _write_json(tmp_path / "package.agent.json", data)
        manifest = load_manifest_universal(tmp_path)
        assert manifest.artifacts is None

    def test_unit_default_new_fields(self, tmp_path: Path) -> None:
        """New UAAPS v0.4.0 fields default correctly when not in manifest."""
        _write_json(tmp_path / "package.agent.json", _minimal_manifest())
        manifest = load_manifest_universal(tmp_path)
        assert manifest.category is None
        assert manifest.engines == {}
        assert manifest.env == {}
        assert manifest.permissions is None
        assert manifest.optional_dependencies == {}
        assert manifest.peer_dependencies == {}
        assert manifest.system_dependencies is None
        assert manifest.resolutions == {}
        assert manifest.dist_tags == {}
        assert manifest.vendor_extensions == {}


################################################################################
#                                                                              #
# TESTS: EnvVarConfig                                                          #
#                                                                              #
################################################################################


class TestEnvVarConfig:
    """Tests for :class:`EnvVarConfig` model validation."""

    def test_unit_env_var_config_required_flag(self) -> None:
        """EnvVarConfig defaults required=True (env vars are required by default)."""
        cfg = EnvVarConfig(description="My var")
        assert cfg.required is True

    def test_unit_env_var_config_required_true(self) -> None:
        """EnvVarConfig can mark a variable as required."""
        cfg = EnvVarConfig(description="Required var", required=True)
        assert cfg.required is True

    def test_unit_manifest_env_loaded_from_json(self, tmp_path: Path) -> None:
        """env dict is loaded from manifest JSON correctly."""
        data = {
            **_minimal_manifest(),
            "env": {
                "OPENAI_API_KEY": {
                    "description": "OpenAI key",
                    "required": True,
                }
            },
        }
        _write_json(tmp_path / "package.agent.json", data)
        manifest = load_manifest_universal(tmp_path)
        assert "OPENAI_API_KEY" in manifest.env
        assert manifest.env["OPENAI_API_KEY"].required is True


################################################################################
#                                                                              #
# TESTS: PermissionsConfig                                                     #
#                                                                              #
################################################################################


class TestPermissionsConfig:
    """Tests for :class:`PermissionsConfig` v0.5.0 structured model validation."""

    def test_unit_permissions_defaults_empty(self) -> None:
        """PermissionsConfig defaults to empty grants and shell=False."""
        perms = PermissionsConfig()
        assert perms.fs.read == []
        assert perms.fs.write == []
        assert perms.network.hosts == []
        assert perms.network.schemes == ["https"]
        assert perms.shell.allow is False
        assert perms.shell.binaries == []

    def test_unit_permissions_loaded_from_manifest_flat(self, tmp_path: Path) -> None:
        """v0.4.0 flat-list permissions are migrated to structured on load."""
        data = {
            **_minimal_manifest(),
            "permissions": {
                "network": ["https://api.openai.com"],
                "fs": ["~/.config/"],
                "shell": True,
            },
        }
        _write_json(tmp_path / "package.agent.json", data)
        manifest = load_manifest_universal(tmp_path)
        assert manifest.permissions is not None
        assert "https://api.openai.com" in manifest.permissions.network.hosts
        assert manifest.permissions.shell.allow is True
        assert "~/.config/" in manifest.permissions.fs.read

    def test_unit_permissions_loaded_structured(self, tmp_path: Path) -> None:
        """v0.5.0 structured permissions are loaded correctly."""
        data = {
            **_minimal_manifest(),
            "permissions": {
                "fs": {"read": ["./src"], "write": ["./dist"]},
                "network": {"hosts": ["api.example.com"], "schemes": ["https"]},
                "shell": {"allow": True, "binaries": ["node"]},
            },
        }
        _write_json(tmp_path / "package.agent.json", data)
        manifest = load_manifest_universal(tmp_path)
        assert manifest.permissions is not None
        assert manifest.permissions.fs.read == ["./src"]
        assert manifest.permissions.fs.write == ["./dist"]
        assert manifest.permissions.network.hosts == ["api.example.com"]
        assert manifest.permissions.shell.allow is True
        assert manifest.permissions.shell.binaries == ["node"]


################################################################################
#                                                                              #
# TESTS: SystemDependencies                                                    #
#                                                                              #
################################################################################


class TestSystemDependencies:
    """Tests for :class:`SystemDependencies` model validation."""

    def test_unit_system_dependencies_defaults(self) -> None:
        """SystemDependencies defaults to empty lists and None versions."""
        sys_deps = SystemDependencies()
        assert sys_deps.python is None
        assert sys_deps.node is None
        assert sys_deps.binaries == []
        assert sys_deps.mcp_servers == []

    def test_unit_system_deps_loaded_from_manifest(self, tmp_path: Path) -> None:
        """systemDependencies block loaded from manifest JSON (camelCase key)."""
        data = {
            **_minimal_manifest(),
            "systemDependencies": {
                "python": ">=3.11",
                "node": ">=18",
                "binaries": ["jq", "curl"],
                "packages": {"pip": ["requests"]},
            },
        }
        _write_json(tmp_path / "package.agent.json", data)
        manifest = load_manifest_universal(tmp_path)
        assert manifest.system_dependencies is not None
        assert manifest.system_dependencies.python == ">=3.11"
        assert manifest.system_dependencies.node == ">=18"
        assert "jq" in manifest.system_dependencies.binaries
        assert "requests" in manifest.system_dependencies.packages.pip


################################################################################
#                                                                              #
# TESTS: v0.5.0 Structured Permissions                                        #
#                                                                              #
################################################################################


class TestStructuredPermissions:
    """Tests for v0.5.0 structured permissions model."""

    def test_unit_default_permissions(self) -> None:
        """Default permissions have empty grants."""
        perms = PermissionsConfig()
        assert perms.fs.read == []
        assert perms.fs.write == []
        assert perms.network.hosts == []
        assert perms.network.schemes == ["https"]
        assert perms.shell.allow is False
        assert perms.shell.binaries == []

    def test_unit_structured_permissions(self) -> None:
        """Fully specified structured permissions parse correctly."""
        perms = PermissionsConfig(
            fs=FsPermissions(read=["./src"], write=["./dist"]),
            network=NetworkPermissions(hosts=["api.example.com"], schemes=["https"]),
            shell=ShellPermissions(allow=True, binaries=["node", "npm"]),
        )
        assert perms.fs.read == ["./src"]
        assert perms.fs.write == ["./dist"]
        assert perms.network.hosts == ["api.example.com"]
        assert perms.shell.allow is True
        assert perms.shell.binaries == ["node", "npm"]

    def test_unit_backward_compat_flat_fs(self) -> None:
        """v0.4.0 flat fs list migrates to structured read grants."""
        perms = PermissionsConfig.model_validate({
            "fs": ["./src", "./lib"],
            "network": ["api.example.com"],
            "shell": True,
        })
        assert perms.fs.read == ["./src", "./lib"]
        assert perms.fs.write == []
        assert perms.network.hosts == ["api.example.com"]
        assert perms.shell.allow is True


################################################################################
#                                                                              #
# TESTS: Prompts-to-Commands Migration                                         #
#                                                                              #
################################################################################


class TestPromptsMerge:
    """Tests for prompts-to-commands migration."""

    def test_unit_prompts_migrated_to_commands(self) -> None:
        """Prompts entries are migrated to commands in ArtifactsDeclaration."""
        arts = ArtifactsDeclaration.model_validate({
            "prompts": [
                {"name": "my-prompt", "path": "prompts/my-prompt.md", "description": "A prompt"}
            ],
            "commands": [
                {"name": "my-cmd", "path": "commands/my-cmd.md", "description": "A command"}
            ],
        })
        assert len(arts.commands) == 2
        assert len(arts.prompts) == 0
        command_names = [c.name for c in arts.commands]
        assert "my-prompt" in command_names
        assert "my-cmd" in command_names

    def test_unit_all_artifacts_excludes_prompts(self) -> None:
        """all_artifacts does not yield prompt tuples."""
        arts = ArtifactsDeclaration(
            commands=[ArtifactRef(name="test-cmd", path="commands/test.md", description="Test")],
        )
        types = [t for t, _ in arts.all_artifacts]
        assert "prompt" not in types
        assert "command" in types


################################################################################
#                                                                              #
# TESTS: installMode                                                           #
#                                                                              #
################################################################################


class TestInstallMode:
    """Tests for installMode manifest field."""

    def test_unit_default_install_mode(self) -> None:
        """Default install mode is 'uaaps'."""
        manifest = PackageManifest(
            name="test-pkg",
            version="1.0.0",
            description="Test package",
        )
        assert manifest.install_mode == "uaaps"

    def test_unit_string_install_mode(self) -> None:
        """String installMode is accepted."""
        manifest = PackageManifest.model_validate({
            "name": "test-pkg",
            "version": "1.0.0",
            "description": "Test package",
            "installMode": "plugin",
        })
        assert manifest.install_mode == "plugin"

    def test_unit_dict_install_mode(self) -> None:
        """Per-platform dict installMode is accepted."""
        manifest = PackageManifest.model_validate({
            "name": "test-pkg",
            "version": "1.0.0",
            "description": "Test package",
            "installMode": {"cursor": "plugin", "claude": "uaaps"},
        })
        assert manifest.install_mode == {"cursor": "plugin", "claude": "uaaps"}


################################################################################
#                                                                              #
# TESTS: Vendor Extension Validation                                           #
#                                                                              #
################################################################################


class TestVendorExtensionValidation:
    """Tests for vendor extension key/value validation."""

    def test_unit_valid_vendor_extension(self) -> None:
        """Valid x-* keys with dict values are accepted."""
        manifest = PackageManifest.model_validate({
            "name": "test-pkg",
            "version": "1.0.0",
            "description": "Test",
            "x-my-vendor": {"key": "value"},
        })
        assert "x-my-vendor" in manifest.vendor_extensions

    def test_unit_invalid_vendor_key_format(self) -> None:
        """Invalid vendor key format is rejected."""
        with pytest.raises(ValidationError):
            PackageManifest.model_validate({
                "name": "test-pkg",
                "version": "1.0.0",
                "description": "Test",
                "x-INVALID": {"key": "value"},
            })

    def test_unit_non_dict_vendor_value_rejected(self) -> None:
        """Non-dict vendor extension values are rejected."""
        with pytest.raises(ValidationError):
            PackageManifest.model_validate({
                "name": "test-pkg",
                "version": "1.0.0",
                "description": "Test",
                "x-my-vendor": "string-value",
            })
