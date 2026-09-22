"""Provider boundary for canonical Curios configuration profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from curios_contracts import ConfigurationProfile, ConfigurationProfileName, Result

type ConfigurationProfileResult = Result[ConfigurationProfile]


def local_docker_configuration_profile() -> ConfigurationProfile:
    """Return the frozen M0 local configuration profile identity."""
    return ConfigurationProfile(
        profile=ConfigurationProfileName.LOCAL_DOCKER,
        description="Local Docker development profile identity.",
    )


@runtime_checkable
class ConfigurationProvider(Protocol):
    """Boundary implemented by replaceable configuration-profile providers."""

    def load_configuration_profile(self) -> ConfigurationProfileResult:
        """Return the canonical configuration profile without resolving secrets."""


@dataclass(frozen=True, slots=True)
class StaticConfigurationProvider:
    """Deterministic configuration provider for the current M0 profile surface."""

    profile: ConfigurationProfile = field(default_factory=local_docker_configuration_profile)

    def __post_init__(self) -> None:
        if not isinstance(self.profile, ConfigurationProfile):
            msg = "profile must be a ConfigurationProfile"
            raise TypeError(msg)

    def load_configuration_profile(self) -> ConfigurationProfileResult:
        """Return the configured canonical profile through the provider boundary."""
        return Result.success(self.profile)


def local_docker_configuration_provider() -> ConfigurationProvider:
    """Return the M0 LOCAL_DOCKER configuration provider."""
    return StaticConfigurationProvider()
