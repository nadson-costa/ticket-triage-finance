"""Configuração do pipeline de geração (ver docs/generation_spec.md, seção 4.2)."""

from .loader import ConfigError, load_config
from .models import (
    CategoryConfig,
    Config,
    GenerationConfig,
    SplitConfig,
    TaxonomyConfig,
)

__all__ = [
    "CategoryConfig",
    "Config",
    "ConfigError",
    "GenerationConfig",
    "SplitConfig",
    "TaxonomyConfig",
    "load_config",
]
