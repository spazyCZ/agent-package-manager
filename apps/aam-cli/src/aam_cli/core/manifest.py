"""Pydantic models for the AAM package manifest (``aam.yaml``).

Defines all data structures needed to parse, validate, and serialize
the package manifest.  Also includes the ``AgentDefinition`` model
used by the Cursor adapter for ``agent.yaml`` files.

Validation uses Pydantic v2 standard validators with regex patterns,
max lengths, and non-empty checks from data-model.md.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
import re
from pathlib import Path

from pydantic import BaseModel, field_validator, model_validator

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

# Maximum description length
MAX_DESCRIPTION_LENGTH: int = 256

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
# PLATFORM & ARTIFACTS DECLARATIONS                                            #
#                                                                              #
################################################################################


class PlatformConfig(BaseModel):
    """Platform-specific deployment configuration."""

    skill_scope: str = "project"
    deploy_instructions_as: str = "rules"
    merge_instructions: bool = False


class ArtifactsDeclaration(BaseModel):
    """All artifact types declared in a package."""

    agents: list[ArtifactRef] = []
    skills: list[ArtifactRef] = []
    prompts: list[ArtifactRef] = []
    instructions: list[ArtifactRef] = []


################################################################################
#                                                                              #
# PACKAGE MANIFEST                                                             #
#                                                                              #
################################################################################


class PackageManifest(BaseModel):
    """Complete ``aam.yaml`` manifest model.

    The manifest is the primary metadata file for an AAM package.
    It declares package identity, artifacts, dependencies, platform
    config, and quality settings.
    """

    name: str
    version: str
    description: str
    author: str | None = None
    license: str | None = None
    repository: str | None = None
    homepage: str | None = None
    keywords: list[str] = []
    artifacts: ArtifactsDeclaration
    dependencies: dict[str, str] = {}
    platforms: dict[str, PlatformConfig] = {}
    quality: QualityConfig | None = None

    # -----
    # Validators
    # -----

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

    @model_validator(mode="after")
    def validate_has_artifacts(self) -> "PackageManifest":
        """Ensure at least one artifact is declared."""
        total = (
            len(self.artifacts.agents)
            + len(self.artifacts.skills)
            + len(self.artifacts.prompts)
            + len(self.artifacts.instructions)
        )
        if total == 0:
            raise ValueError("At least one artifact must be declared across all types")
        return self

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate dependency names and constraint syntax."""
        for dep_name, constraint in v.items():
            if not _FULL_NAME_PATTERN.match(dep_name):
                raise ValueError(
                    f"Invalid dependency name '{dep_name}': must match {FULL_NAME_REGEX}"
                )
            # Validate constraint syntax
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
        """Flat list of ``(type, ref)`` tuples."""
        result: list[tuple[str, ArtifactRef]] = []
        for agent in self.artifacts.agents:
            result.append(("agent", agent))
        for skill in self.artifacts.skills:
            result.append(("skill", skill))
        for prompt in self.artifacts.prompts:
            result.append(("prompt", prompt))
        for instruction in self.artifacts.instructions:
            result.append(("instruction", instruction))
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
    prompts: list[str] = []
    tools: list[str] = []
    parameters: dict[str, str | int | float | bool] = {}


################################################################################
#                                                                              #
# LOADING HELPERS                                                              #
#                                                                              #
################################################################################


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
