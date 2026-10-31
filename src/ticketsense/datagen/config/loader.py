from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .models import Config


class ConfigError(Exception):
    """Configuração ausente, malformada ou inconsistente."""


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise ConfigError(f"Arquivo de configuração não encontrado: {path}") from e
    except yaml.YAMLError as e:
        raise ConfigError(f"YAML inválido em {path}: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"{path} deve ter chaves e valores na raiz do arquivo")
    return data


def load_config(
    taxonomy_path: str | Path = "configs/taxonomy.yaml",
    generation_path: str | Path = "configs/generation.yaml",
) -> Config:
    taxonomy = _read_yaml(Path(taxonomy_path))
    generation = _read_yaml(Path(generation_path))
    try:
        return Config(taxonomy=taxonomy, generation=generation)
    except ValidationError as e:
        raise ConfigError(f"Configuração inválida:\n{e}") from e
