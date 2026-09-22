"""Configuration provider boundary for Curios."""

from curios_config.provider import (
    ConfigurationProfileResult,
    ConfigurationProvider,
    StaticConfigurationProvider,
    local_docker_configuration_profile,
    local_docker_configuration_provider,
)

__version__ = "0.0.0"

__all__ = (
    "ConfigurationProfileResult",
    "ConfigurationProvider",
    "StaticConfigurationProvider",
    "__version__",
    "local_docker_configuration_profile",
    "local_docker_configuration_provider",
)
