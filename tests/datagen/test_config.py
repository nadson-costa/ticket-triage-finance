import re
from collections.abc import Callable
from pathlib import Path

import pytest

from ticketsense.datagen.config import Config, ConfigError, load_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_PATH = PROJECT_ROOT / "configs" / "taxonomy.yaml"
GENERATION_PATH = PROJECT_ROOT / "configs" / "generation.yaml"

WriteConfigs = Callable[[str, str], tuple[Path, Path]]


def replace_once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, f"trecho esperado exatamente uma vez no YAML: {old!r}"
    return text.replace(old, new)


@pytest.fixture
def taxonomy_text() -> str:
    return TAXONOMY_PATH.read_text(encoding="utf-8")


@pytest.fixture
def generation_text() -> str:
    return GENERATION_PATH.read_text(encoding="utf-8")


@pytest.fixture
def write_configs(tmp_path: Path) -> WriteConfigs:
    """Grava dois textos YAML em arquivos temporários e devolve os caminhos."""

    def _write(taxonomy: str, generation: str) -> tuple[Path, Path]:
        taxonomy_path = tmp_path / "taxonomy.yaml"
        generation_path = tmp_path / "generation.yaml"
        taxonomy_path.write_text(taxonomy, encoding="utf-8")
        generation_path.write_text(generation, encoding="utf-8")
        return taxonomy_path, generation_path

    return _write


# --------------------------------------------------------------------------- #
# Arquivos reais do projeto
# --------------------------------------------------------------------------- #


def test_real_configs_load():
    config = load_config(TAXONOMY_PATH, GENERATION_PATH)

    assert isinstance(config, Config)
    assert config.taxonomy.version == "1.1"
    assert len(config.taxonomy.categories) == 8
    assert set(config.generation.splits) == {"train", "val", "test_gen_b"}


def test_default_paths_work_from_project_root(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(PROJECT_ROOT)

    config = load_config()

    assert isinstance(config, Config)


def test_urgency_criteria_keys_are_integers():
    config = load_config(TAXONOMY_PATH, GENERATION_PATH)

    assert set(config.taxonomy.urgency_criteria) == {1, 2, 3, 4, 5}


def test_length_ranges_are_tuples():
    config = load_config(TAXONOMY_PATH, GENERATION_PATH)

    assert config.generation.length_words.curto == (4, 25)


def test_fingerprint_is_stable_across_loads():
    first = load_config(TAXONOMY_PATH, GENERATION_PATH)
    second = load_config(TAXONOMY_PATH, GENERATION_PATH)

    assert first.fingerprint() == second.fingerprint()
    assert len(first.fingerprint()) == 64


def test_fingerprint_changes_when_a_value_changes(
    taxonomy_text: str, generation_text: str, write_configs: WriteConfigs
):
    original = load_config(TAXONOMY_PATH, GENERATION_PATH)
    changed_generation = replace_once(generation_text, "seed: 42", "seed: 43")

    changed = load_config(*write_configs(taxonomy_text, changed_generation))

    assert changed.fingerprint() != original.fingerprint()


# --------------------------------------------------------------------------- #
# Problemas de leitura
# --------------------------------------------------------------------------- #


def test_missing_file_is_reported(tmp_path: Path):
    with pytest.raises(ConfigError, match="não encontrado"):
        load_config(tmp_path / "nao_existe.yaml", GENERATION_PATH)


@pytest.mark.parametrize("content", ["", "- a\n- b\n", "texto solto"])
def test_yaml_without_mapping_at_root_is_rejected(
    content: str, generation_text: str, write_configs: WriteConfigs
):
    paths = write_configs(content, generation_text)

    with pytest.raises(ConfigError, match="deve ter chaves e valores"):
        load_config(*paths)


def test_malformed_yaml_is_reported(generation_text: str, write_configs: WriteConfigs):
    paths = write_configs("categorias: [1, 2\nversao: 3", generation_text)

    with pytest.raises(ConfigError, match="YAML inválido"):
        load_config(*paths)


# --------------------------------------------------------------------------- #
# Validação da taxonomia
# --------------------------------------------------------------------------- #

PIX_CONFUSABLE = "confusable_with: [fraude_seguranca]\n\n  cartoes:"

INVALID_TAXONOMY_CASES = [
    pytest.param("share: 0.22", "share: 0.30", "soma dos 'share'", id="share-nao-soma-um"),
    pytest.param(
        PIX_CONFUSABLE,
        "confusable_with: [banana]\n\n  cartoes:",
        "confusable_with 'banana' não existe",
        id="confusable-inexistente",
    ),
    pytest.param(
        PIX_CONFUSABLE,
        "confusable_with: [pix]\n\n  cartoes:",
        "não pode incluir ela mesma",
        id="confusable-com-ela-mesma",
    ),
    pytest.param(
        "urgency_criteria: [1, 3, 4, 5]",
        "urgency_criteria: [1, 3, 4, 9]",
        "critério de urgência 9",
        id="criterio-de-urgencia-inexistente",
    ),
    pytest.param(
        "{id: usuario_iniciante, weight: 2}",
        "{id: cliente_comum, weight: 2}",
        "ids repetidos",
        id="ids-repetidos-nos-estilos",
    ),
    pytest.param(
        "{id: curto, weight: 4}",
        "{id: enorme, weight: 4}",
        "ids inválidos",
        id="tamanho-invalido-nos-estilos",
    ),
    pytest.param('"<CPF>"', '"CPF"', "should match pattern", id="placeholder-mal-formado"),
    pytest.param(
        "    share: 0.22\n",
        "    share: 0.22\n    shar: 1\n",
        "Extra inputs are not permitted",
        id="chave-desconhecida-na-categoria",
    ),
]


@pytest.mark.parametrize(("old", "new", "message"), INVALID_TAXONOMY_CASES)
def test_invalid_taxonomy_is_rejected(
    old: str,
    new: str,
    message: str,
    taxonomy_text: str,
    generation_text: str,
    write_configs: WriteConfigs,
):
    paths = write_configs(replace_once(taxonomy_text, old, new), generation_text)

    with pytest.raises(ConfigError, match=re.escape(message)):
        load_config(*paths)


def test_all_taxonomy_problems_are_reported_together(
    taxonomy_text: str, generation_text: str, write_configs: WriteConfigs
):
    broken = replace_once(taxonomy_text, "share: 0.22", "share: 0.30")
    broken = replace_once(broken, PIX_CONFUSABLE, "confusable_with: [banana]\n\n  cartoes:")
    paths = write_configs(broken, generation_text)

    with pytest.raises(ConfigError) as error:
        load_config(*paths)

    assert "soma dos 'share'" in str(error.value)
    assert "confusable_with 'banana' não existe" in str(error.value)


# --------------------------------------------------------------------------- #
# Validação dos parâmetros de geração
# --------------------------------------------------------------------------- #

INVALID_GENERATION_CASES = [
    pytest.param("oversample:", "oversmple:", "oversmple", id="chave-com-erro-de-digitacao"),
    pytest.param(
        "oversample: 1.3",
        "oversample: 0.5",
        "greater than or equal to 1",
        id="excedente-abaixo-de-1",
    ),
    pytest.param(
        "vague: 0.04", "vague: 4", "less than or equal to 1", id="probabilidade-acima-de-1"
    ),
    pytest.param("n: 8000", "n: 0", "greater than 0", id="tamanho-do-split-zero"),
    pytest.param("generator: B", "generator: C", "Input should be", id="gerador-do-split-invalido"),
    pytest.param("priority: 3", "priority: 4", "priority", id="prioridades-repetidas"),
    pytest.param(
        "curto: [4, 25]", "curto: [4, 40]", "não podem se sobrepor", id="faixas-que-se-sobrepoem"
    ),
    pytest.param(
        "curto: [4, 25]", "curto: [30, 25]", "maior que máximo", id="faixa-com-minimo-maior"
    ),
    pytest.param(
        '  B:\n    name: "gpt-4.1-mini"',
        '  C:\n    name: "gpt-4.1-mini"',
        "não tem modelo",
        id="gerador-sem-modelo",
    ),
    pytest.param(
        'name: "gpt-5.4-nano"',
        'name: "modelo-sem-preco"',
        "não tem preço",
        id="modelo-sem-preco",
    ),
    pytest.param("budget_usd: 15.0", "budget_usd: 0", "greater than 0", id="orcamento-zero"),
    pytest.param("threshold: 0.90", "threshold: 0", "greater than 0", id="limiar-de-dedup-zero"),
    pytest.param(
        "vague: 0.04",
        "vague: 0.04\n  vagu: 1",
        "Extra inputs are not permitted",
        id="chave-desconhecida-nas-taxas",
    ),
]


@pytest.mark.parametrize(("old", "new", "message"), INVALID_GENERATION_CASES)
def test_invalid_generation_is_rejected(
    old: str,
    new: str,
    message: str,
    taxonomy_text: str,
    generation_text: str,
    write_configs: WriteConfigs,
):
    paths = write_configs(taxonomy_text, replace_once(generation_text, old, new))

    with pytest.raises(ConfigError, match=re.escape(message)):
        load_config(*paths)


# --------------------------------------------------------------------------- #
# Consistência entre os dois arquivos
# --------------------------------------------------------------------------- #


def test_generator_missing_from_taxonomy_is_rejected(
    taxonomy_text: str, generation_text: str, write_configs: WriteConfigs
):
    broken = replace_once(taxonomy_text, "  B:\n    personas:", "  C:\n    personas:")
    paths = write_configs(broken, generation_text)

    with pytest.raises(ConfigError, match="não existe em taxonomy.generators"):
        load_config(*paths)
