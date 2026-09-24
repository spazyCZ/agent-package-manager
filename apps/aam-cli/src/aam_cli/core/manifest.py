"""Pydantic models for the AAM package manifest (``aam.yaml``).

Defines all data structures needed to parse, validate, and serialize
the package manifest.  Also includes the ``AgentDefinition`` model
used by the Cursor adapter for ``agent.yaml`` files.

Validation uses Pydantic v2 standard validators with regex patterns,
max lengths, and non-empty checks from data-model.md.

Updated for UAAPS v0.5.0-draft: structured permissions, prompt→command
migration, vendor extension validation, and installMode field.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aam_cli.utils.naming import FULL_NAME_REGEX, NAME_REGEX

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# CONSTANTS                                                                    #
#                                                                              #
################################################################################

# Pre-compiled patterns for field validation
_NAME_PATTERN = re.compile(NAME_REGEX)
_FULL_NAME_PATTERN = re.compile(FULL_NAME_REGEX)

# Maximum description length (updated for UAAPS v0.4.0)
MAX_DESCRIPTION_LENGTH: int = 1024

################################################################################
#                                                                              #
# UAAPS v0.5.0 SUB-MODELS                                                     #
#                                                                              #
################################################################################


class EnvVarConfig(BaseModel):
    """Configuration for a required or optional environment variable."""

    description: str
    required: bool = True
    default: str | None = None


class FsPermissions(BaseModel):
    """Filesystem permission scopes with distinct read/write grants."""

    read: list[str] = []
    write: list[str] = []


class NetworkPermissions(BaseModel):
    """Network access permissions with host and scheme scoping."""

    hosts: list[str] = []
    schemes: list[str] = Field(default_factory=lambda: ["https"])


class ShellPermissions(BaseModel):
    """Shell execution permissions with binary allow-list."""

    allow: bool = False
    binaries: list[str] = []


class PermissionsConfig(BaseModel):
    """Requested capability permissions for the package.

    v0.5.0 structured format. Accepts v0.4.0 flat-list format via
    backward-compatibility migration in the model validator.
    """

    fs: FsPermissions = Field(default_factory=FsPermissions)
    network: NetworkPermissions = Field(default_factory=NetworkPermissions)
    shell: ShellPermissions = Field(default_factory=ShellPermissions)

    @model_validator(mode="before")
    @classmethod
    def migrate_flat_format(cls, data: Any) -> Any:
        """Migrate v0.4.0 flat-list format to v0.5.0 structured format."""
        if not isinstance(data, dict):
            return data
        if "fs" in data and isinstance(data["fs"], list):
            data["fs"] = {"read": data["fs"], "write": []}
        if "network" in data and isinstance(data["network"], list):
            data["network"] = {"hosts": data["network"], "schemes": ["https"]}
        if "shell" in data and isinstance(data["shell"], bool):
            data["shell"] = {"allow": data["shell"], "binaries": []}
        return data


class SystemPackages(BaseModel):
    """Package-manager-level system dependencies."""

    pip: list[str] = []
    npm: list[str] = []
    brew: list[str] = []
    apt: list[str] = []
    cargo: list[str] = []


class SystemDependencies(BaseModel):
    """OS-level and runtime system requirements."""

    model_config = ConfigDict(populate_by_name=True)

    python: str | None = None
    node: str | None = None
    packages: SystemPackages = SystemPackages()
    binaries: list[str] = []
    mcp_servers: list[str] = Field(
        default_factory=list,
        validation_alias="mcp-servers",
        serialization_alias="mcp-servers",
    )


################################################################################
#                                                                              #
# ARTIFACT MODELS                                                              #
#                                                                              #
################################################################################


class ArtifactRef(BaseModel):
    """Reference to a single artifact within a package."""

    name: str
    path: str
    description: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate artifact name matches ``^[a-z0-9][a-z0-9-]{0,63}$``."""
        if not _NAME_PATTERN.match(v):
            raise ValueError(f"Invalid artifact name '{v}': must match {NAME_REGEX}")
        return v

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate artifact path is relative with no directory traversal."""
        if v.startswith("/"):
            raise ValueError(f"Artifact path must be relative, got absolute path: '{v}'")
        if ".." in Path(v).parts:
            raise ValueError(f"Artifact path must not use '..': '{v}'")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is not empty and within max length."""
        if len(v) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(f"Description exceeds {MAX_DESCRIPTION_LENGTH} characters")
        return v


################################################################################
#                                                                              #
# QUALITY MODELS                                                               #
#                                                                              #
################################################################################


class QualityTest(BaseModel):
    """Declared test in quality section."""

    name: str
    command: str
    description: str


class EvalMetric(BaseModel):
    """Metric definition within an eval."""

    name: str
    type: str  # percentage, score, duration_ms, boolean


class QualityEval(BaseModel):
    """Declared eval in quality section."""

    name: str
    path: str
    description: str
    metrics: list[EvalMetric] = []


class QualityConfig(BaseModel):
    """Quality section of aam.yaml."""

    tests: list[QualityTest] = []
    evals: list[QualityEval] = []


################################################################################
#                                                                              #
# PROVENANCE                                                                   #
#                                                                              #
################################################################################


class Provenance(BaseModel):
    """Tracks where a package's artifacts originated.

    Added to ``aam.yaml`` when a package is created from a remote
    source via ``aam create-package --from-source``.
    """

    source_type: Literal["git", "local"] = "local"
    source_url: str | None = None  # Clone URL
    source_ref: str | None = None  # Branch/tag/commit
    source_path: str | None = None  # Scan scope
    source_commit: str | None = None  # Commit SHA at time of creation
    fetched_at: str | None = None  # ISO 8601 timestamp


################################################################################
#                                                                              #
# PLATFORM & ARTIFACTS DECLARATIONS                                            #
#                                                                              #
################################################################################


class PlatformConfig(BaseModel):
    """Platform-specific deployment configuration."""

    skill_scope: str = "project"
    deploy_instructions_as: str = "rules"
    merge_instructions: bool = False


class ArtifactsDeclaration(BaseModel):
    """All artifact types declared in or discovered for a package."""

    # Existing types (unchanged)
    agents: list[ArtifactRef] = []
    skills: list[ArtifactRef] = []
    prompts: list[ArtifactRef] = []  # DEPRECATED — migrated to commands
    instructions: list[ArtifactRef] = []  # legacy — kept for aam.yaml compat

    # New artifact types (UAAPS v0.4.0+)
    commands: list[ArtifactRef] = []
    rules: list[ArtifactRef] = []  # UAAPS extension (not in spec §3 artifacts)
    hooks_path: str | None = None
    mcp_path: str | None = None

    @model_validator(mode="before")
    @classmethod
    def migrate_prompts_to_commands(cls, data: Any) -> Any:
        """Migrate legacy prompts entries into commands (UAAPS v0.5.0)."""
        if isinstance(data, dict) and "prompts" in data:
            prompts = data.get("prompts", [])
            if prompts:
                commands = data.get("commands", [])
                commands.extend(prompts)
                data["commands"] = commands
                data["prompts"] = []
        return data

    @property
    def all_artifacts(self) -> list[tuple[str, "ArtifactRef"]]:
        """Return all (type, ref) pairs for path-based artifact types.

        Returns:
            List of ``(artifact_type, ArtifactRef)`` tuples in consistent order.
        """
        results: list[tuple[str, ArtifactRef]] = []
        for ref in self.skills:
            results.append(("skill", ref))
        for ref in self.agents:
            results.append(("agent", ref))
        for ref in self.instructions:
            results.append(("instruction", ref))
        for ref in self.commands:
            results.append(("command", ref))
        for ref in self.rules:
            results.append(("rule", ref))
        return results


################################################################################
#                                                                              #
# PACKAGE MANIFEST                                                             #
#                                                                              #
################################################################################


class PackageManifest(BaseModel):
    """Universal package manifest — supports package.agent.json, package.agent.yaml, aam.yaml.

    The manifest is the primary metadata file for an AAM package.
    It declares package identity, artifacts, dependencies, platform
    config, quality settings, and UAAPS v0.5.0 fields.

    JSON field names use camelCase/hyphenated keys per UAAPS spec;
    Python attributes use snake_case. Pydantic aliases bridge the gap.
    """

    model_config = ConfigDict(populate_by_name=True)

    # --- EXISTING REQUIRED FIELDS (unchanged) ---
    name: str
    version: str
    description: str

    # --- EXISTING OPTIONAL FIELDS (unchanged) ---
    author: str | None = None
    license: str | None = None
    repository: str | None = None
    homepage: str | None = None
    keywords: list[str] = []
    platforms: dict[str, PlatformConfig] = {}
    quality: QualityConfig | None = None

    # --- EXISTING DEPENDENCY FIELD (unchanged) ---
    dependencies: dict[str, str] = {}

    # --- Source provenance metadata (spec 003) ---
    provenance: Provenance | None = None

    # --- ARTIFACTS (now optional — auto-discovered if absent) ---
    artifacts: ArtifactsDeclaration | None = None

    # --- NEW UAAPS v0.4.0 FIELDS ---
    category: str | None = None
    engines: dict[str, str] = {}
    env: dict[str, EnvVarConfig] = {}
    permissions: PermissionsConfig | None = None

    optional_dependencies: dict[str, str] = Field(
        default_factory=dict, alias="optionalDependencies"
    )
    peer_dependencies: dict[str, str] = Field(
        default_factory=dict, alias="peerDependencies"
    )
    system_dependencies: SystemDependencies | None = Field(
        default=None, alias="systemDependencies"
    )
    resolutions: dict[str, str] = {}
    dist_tags: dict[str, str] = Field(
        default_factory=dict, alias="dist-tags"
    )
    install_mode: dict[str, str] | str = Field(
        default="uaaps", alias="installMode"
    )

    # Component path overrides (default = convention)
    skills_path: str = Field(default="./skills", alias="skills")
    commands_path: str = Field(default="./commands", alias="commands")
    agents_path: str = Field(default="./agents", alias="agents")
    rules_path: str = Field(default="./rules", alias="rules")
    hooks_path: str = Field(default="./hooks/hooks.json", alias="hooks")
    mcp_path: str = Field(default="./mcp/servers.json", alias="mcp")

    # Vendor extensions (x-* fields)
    vendor_extensions: dict[str, Any] = {}

    # MANIFEST FORMAT SENTINEL — set by loader, not from file
    manifest_format: Literal["json", "yaml", "legacy"] = "legacy"

    # -----
    # Validators
    # -----

    @model_validator(mode="before")
    @classmethod
    def collect_vendor_extensions(cls, data: Any) -> Any:
        """Collect and validate all x-* prefixed keys into vendor_extensions."""
        if isinstance(data, dict):
            import re as _re

            vendor = {}
            keys_to_remove = []
            _vendor_key_pattern = _re.compile(r"^x-[a-z0-9][a-z0-9-]{0,31}$")
            for key in data:
                if isinstance(key, str) and key.startswith("x-"):
                    if not _vendor_key_pattern.match(key):
                        raise ValueError(
                            f"Vendor extension key '{key}' must match "
                            "x-[a-z0-9][a-z0-9-]{{0,31}}"
                        )
                    if not isinstance(data[key], dict):
                        raise ValueError(
                            f"Vendor extension '{key}' value must be a JSON "
                            f"object, got {type(data[key]).__name__}"
                        )
                    vendor[key] = data[key]
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del data[key]
            if vendor:
                data["vendor_extensions"] = vendor
        return data

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate full package name matches ``FULL_NAME_REGEX``."""
        if not _FULL_NAME_PATTERN.match(v):
            raise ValueError(f"Invalid package name '{v}': must match {FULL_NAME_REGEX}")
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version is valid semver (parseable by packaging)."""
        from aam_cli.core.version import parse_version

        parse_version(v)  # raises ValueError if invalid
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is non-empty and within max length."""
        if not v.strip():
            raise ValueError("Description must not be empty")
        if len(v) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(f"Description exceeds {MAX_DESCRIPTION_LENGTH} characters")
        return v

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate dependency names and constraint syntax."""
        for dep_name, constraint in v.items():
            if not _FULL_NAME_PATTERN.match(dep_name):
                raise ValueError(
                    f"Invalid dependency name '{dep_name}': must match {FULL_NAME_REGEX}"
                )
            from aam_cli.core.version import parse_constraint

            parse_constraint(constraint)
        return v

    @field_validator("optional_dependencies")
    @classmethod
    def validate_optional_dependencies(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate optional dependency names and constraint syntax."""
        for dep_name, constraint in v.items():
            if not _FULL_NAME_PATTERN.match(dep_name):
                raise ValueError(
                    f"Invalid optional dependency name '{dep_name}': "
                    f"must match {FULL_NAME_REGEX}"
                )
            from aam_cli.core.version import parse_constraint

            parse_constraint(constraint)
        return v

    @field_validator("peer_dependencies")
    @classmethod
    def validate_peer_dependencies(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate peer dependency names and constraint syntax."""
        for dep_name, constraint in v.items():
            if not _FULL_NAME_PATTERN.match(dep_name):
                raise ValueError(
                    f"Invalid peer dependency name '{dep_name}': "
                    f"must match {FULL_NAME_REGEX}"
                )
            from aam_cli.core.version import parse_constraint

            parse_constraint(constraint)
        return v

    # -----
    # Computed properties
    # -----

    @property
    def scope(self) -> str:
        """Extract scope from name. Empty string for unscoped."""
        from aam_cli.utils.naming import parse_package_name

        scope_val, _ = parse_package_name(self.name)
        return scope_val

    @property
    def base_name(self) -> str:
        """Extract base name without scope."""
        from aam_cli.utils.naming import parse_package_name

        _, base = parse_package_name(self.name)
        return base

    @property
    def all_artifacts(self) -> list[tuple[str, ArtifactRef]]:
        """Flat list of ``(type, ref)`` tuples across all artifact types."""
        if self.artifacts is None:
            return []
        result: list[tuple[str, ArtifactRef]] = []
        for agent in self.artifacts.agents:
            result.append(("agent", agent))
        for skill in self.artifacts.skills:
            result.append(("skill", skill))
        for instruction in self.artifacts.instructions:
            result.append(("instruction", instruction))
        for command in self.artifacts.commands:
            result.append(("command", command))
        for rule in self.artifacts.rules:
            result.append(("rule", rule))
        return result

    @property
    def artifact_count(self) -> int:
        """Total number of declared artifacts."""
        return len(self.all_artifacts)


################################################################################
#                                                                              #
# AGENT DEFINITION                                                             #
#                                                                              #
################################################################################


class AgentDefinition(BaseModel):
    """Agent definition file model (``agent.yaml``).

    Used by the Cursor adapter to read agent definitions and convert
    them to ``.mdc`` rule files.
    """

    name: str
    description: str
    version: str | None = None
    system_prompt: str  # Relative path to system-prompt.md
    skills: list[str] = []
    commands: list[str] = []  # was: prompts (UAAPS v0.5.0)
    tools: list[str] = []
    parameters: dict[str, str | int | float | bool] = {}


################################################################################
#                                                                              #
# LOADING HELPERS                                                              #
#                                                                              #
################################################################################


def load_manifest_universal(path: Path) -> PackageManifest:
    """Load and validate a manifest from any supported format.

    Tries ``package.agent.json`` → ``package.agent.yaml`` → ``aam.yaml``
    when given a directory. Sets ``manifest_format`` sentinel on the result.

    Args:
        path: Path to a manifest file or directory containing one.

    Returns:
        Validated :class:`PackageManifest` instance.

    Raises:
        FileNotFoundError: If no manifest file is found.
        ValueError: If the manifest fails validation.
    """
    from aam_cli.utils.paths import MANIFEST_JSON, MANIFEST_LEGACY, MANIFEST_YAML

    logger.info(f"Loading universal manifest: path='{path}'")

    # -----
    # If path is a file, use it directly
    # -----
    if path.is_file():
        manifest_path = path
        if path.name == MANIFEST_JSON:
            fmt: Literal["json", "yaml", "legacy"] = "json"
        elif path.name == MANIFEST_YAML:
            fmt = "yaml"
        else:
            fmt = "legacy"
    elif path.is_dir():
        # -----
        # Deterministic precedence: JSON > YAML > legacy
        # -----
        json_path = path / MANIFEST_JSON
        yaml_path = path / MANIFEST_YAML
        legacy_path = path / MANIFEST_LEGACY

        if json_path.is_file():
            manifest_path = json_path
            fmt = "json"
        elif yaml_path.is_file():
            manifest_path = yaml_path
            fmt = "yaml"
        elif legacy_path.is_file():
            manifest_path = legacy_path
            fmt = "legacy"
        else:
            raise FileNotFoundError(
                f"No manifest found in {path}. "
                f"Expected one of: {MANIFEST_JSON}, {MANIFEST_YAML}, {MANIFEST_LEGACY}"
            )
    else:
        raise FileNotFoundError(f"Path does not exist: {path}")

    # -----
    # Parse based on format
    # -----
    if fmt == "json":
        import json

        text = manifest_path.read_text(encoding="utf-8")
        data = json.loads(text)
    else:
        from aam_cli.utils.yaml_utils import load_yaml

        data = load_yaml(manifest_path)

    data["manifest_format"] = fmt
    manifest = PackageManifest.model_validate(data)

    logger.info(
        f"Universal manifest loaded: name='{manifest.name}', "
        f"version='{manifest.version}', format='{fmt}', "
        f"artifacts={manifest.artifact_count}"
    )
    return manifest


def load_manifest(path: Path) -> PackageManifest:
    """Load and validate a ``PackageManifest`` from an ``aam.yaml`` file.

    Args:
        path: Path to the ``aam.yaml`` file or the directory containing it.

    Returns:
        Validated :class:`PackageManifest` instance.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        ValueError: If the manifest fails validation.
    """
    logger.info(f"Loading package manifest: path='{path}'")

    # -----
    # Resolve to aam.yaml if a directory was given
    # -----
    manifest_path = path if path.name == "aam.yaml" else path / "aam.yaml"

    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"No aam.yaml found at {manifest_path}. Run 'aam create-package' or 'aam init' first."
        )

    from aam_cli.utils.yaml_utils import load_yaml

    data = load_yaml(manifest_path)

    manifest = PackageManifest(**data)
    logger.info(
        f"Manifest loaded: name='{manifest.name}', "
        f"version='{manifest.version}', "
        f"artifacts={manifest.artifact_count}"
    )
    return manifest
